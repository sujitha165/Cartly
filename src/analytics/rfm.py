"""
Cartly Customer Analytics & RFM Segmentation Module
Calculates Recency, Frequency, Monetary (RFM) metrics and performs
transparent, configurable customer segmentation.
"""

from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np


# Standard default RFM segment mapping matrix
# Segments: Champions, Loyal Customers, Potential Loyalists, At Risk, Hibernating, etc.
SEGMENT_DESCRIPTIONS = {
    "Champions": "High recency, high frequency, and high monetary spend. Most valuable brand advocates.",
    "Loyal Customers": "Consistent repeat purchasers with solid lifetime spend. Responsive to loyalty perks.",
    "Potential Loyalists": "Recent buyers with moderate frequency. High potential to convert to champions.",
    "Promising / Recent": "Recent first-time or low-frequency buyers who need nurturing.",
    "Needs Attention": "Above average frequency and spend, but haven't purchased recently.",
    "At Risk": "High spenders in the past who have not purchased in a long time. Immediate retention needed.",
    "Hibernating": "Low recency, low frequency, and low spend. Dormant customers."
}


def calculate_rfm_metrics(
    df: pd.DataFrame,
    reference_date: Optional[pd.Timestamp] = None
) -> pd.DataFrame:
    """
    Compute customer-level Recency (days), Frequency (orders), and Monetary (net spend).
    Only valid purchases (non-cancelled orders) are used for Recency and Frequency.
    Net spend accounts for returns.
    """
    if df.empty:
        return pd.DataFrame(columns=["CustomerID", "Recency", "Frequency", "Monetary", "FirstPurchase", "LastPurchase", "Country"])

    # Reference date is latest date + 1 day if not supplied
    if reference_date is None:
        ref_dt = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    else:
        ref_dt = pd.to_datetime(reference_date)

    sales_df = df[(~df["IsCancelled"]) & (df["Quantity"] > 0)]

    # Compute recency, frequency, and first/last purchase on valid sales
    cust_sales = sales_df.groupby("Customer ID").agg(
        LastPurchase=("InvoiceDate", "max"),
        FirstPurchase=("InvoiceDate", "min"),
        Frequency=("Invoice", "nunique"),
        Country=("Country", "first")
    ).reset_index()

    cust_sales["Recency"] = (ref_dt - cust_sales["LastPurchase"]).dt.days

    # Compute net monetary spend across all transactions (including returns)
    cust_monetary = df.groupby("Customer ID")["LineTotal"].sum().reset_index()
    cust_monetary = cust_monetary.rename(columns={"LineTotal": "Monetary"})
    cust_monetary["Monetary"] = cust_monetary["Monetary"].round(2)

    # Merge
    rfm = pd.merge(cust_sales, cust_monetary, on="Customer ID", how="inner")
    rfm = rfm.rename(columns={"Customer ID": "CustomerID"})

    # Filter out customers with non-positive monetary spend if any
    rfm["Monetary"] = rfm["Monetary"].clip(lower=0.01)

    return rfm


def score_rfm(
    rfm_df: pd.DataFrame,
    q: int = 5
) -> pd.DataFrame:
    """
    Assign R, F, M scores from 1 to 5 using quantiles or rank bins.
    R score: 5 is most recent (lowest recency days), 1 is least recent.
    F score: 5 is highest frequency, 1 is lowest.
    M score: 5 is highest monetary spend, 1 is lowest.
    """
    if rfm_df.empty:
        return rfm_df

    scored = rfm_df.copy()

    # Recency: lower days is better -> invert ranks
    scored["R_Score"] = pd.qcut(
        scored["Recency"].rank(method="first"),
        q=q,
        labels=[5, 4, 3, 2, 1]
    ).astype(int)

    # Frequency: higher is better
    scored["F_Score"] = pd.qcut(
        scored["Frequency"].rank(method="first"),
        q=q,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    # Monetary: higher is better
    scored["M_Score"] = pd.qcut(
        scored["Monetary"].rank(method="first"),
        q=q,
        labels=[1, 2, 3, 4, 5]
    ).astype(int)

    scored["RFM_Score"] = (
        scored["R_Score"].astype(str) +
        scored["F_Score"].astype(str) +
        scored["M_Score"].astype(str)
    )

    return scored


def segment_customers(
    scored_rfm_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Assign intuitive customer segment based on transparent R and F/M score rules.
    """
    if scored_rfm_df.empty:
        return scored_rfm_df

    df = scored_rfm_df.copy()

    def assign_segment(row):
        r = row["R_Score"]
        f = row["F_Score"]
        m = row["M_Score"]
        fm_avg = (f + m) / 2.0

        if r >= 4 and fm_avg >= 4:
            return "Champions"
        elif r >= 3 and fm_avg >= 3:
            return "Loyal Customers"
        elif r >= 4 and fm_avg < 3:
            return "Potential Loyalists"
        elif r >= 3 and fm_avg < 2:
            return "Promising / Recent"
        elif r <= 2 and fm_avg >= 3.5:
            return "At Risk"
        elif r == 2 and 2 <= fm_avg < 3.5:
            return "Needs Attention"
        else:
            return "Hibernating"

    df["Segment"] = df.apply(assign_segment, axis=1)
    df["SegmentDescription"] = df["Segment"].map(SEGMENT_DESCRIPTIONS)
    return df


def get_rfm_segment_summary(segmented_df: pd.DataFrame) -> pd.DataFrame:
    """Compute aggregate business metrics per customer segment."""
    if segmented_df.empty:
        return pd.DataFrame()

    total_customers = len(segmented_df)
    total_rev = segmented_df["Monetary"].sum()

    summary = segmented_df.groupby("Segment").agg(
        CustomerCount=("CustomerID", "count"),
        AvgRecencyDays=("Recency", "mean"),
        AvgFrequency=("Frequency", "mean"),
        AvgMonetary=("Monetary", "mean"),
        TotalMonetary=("Monetary", "sum")
    ).reset_index()

    summary["CustomerSharePct"] = (summary["CustomerCount"] / total_customers * 100).round(1)
    summary["RevenueSharePct"] = (summary["TotalMonetary"] / max(total_rev, 1) * 100).round(1)
    summary["AvgRecencyDays"] = summary["AvgRecencyDays"].round(1)
    summary["AvgFrequency"] = summary["AvgFrequency"].round(1)
    summary["AvgMonetary"] = summary["AvgMonetary"].round(2)
    summary["TotalMonetary"] = summary["TotalMonetary"].round(2)

    return summary.sort_values("TotalMonetary", ascending=False).reset_index(drop=True)
