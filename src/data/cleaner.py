"""
Cartly Data Cleaning and Financial Accuracy Module
Handles cancellation detection, returns separation, deduplication,
missing value handling, and accurate financial calculations.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd


def clean_retail_data(
    df: pd.DataFrame,
    drop_missing_customers: bool = True
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clean retail transactions and enforce financial accuracy.
    
    Steps performed:
    1. Standardize types (InvoiceDate to datetime, Price/Quantity to numeric)
    2. Identify and flag cancellations (Invoice starts with 'C' or 'c')
    3. Remove zero or negative unit prices (data anomalies / write-offs)
    4. Remove duplicate transaction rows
    5. Handle missing descriptions (fill 'Unknown Item')
    6. Calculate LineTotal, GrossSales, and Returns
    7. Optionally filter out null Customer IDs (for customer-level analytics)
    
    Returns:
        (cleaned_df, cleaning_report_dict)
    """
    report: Dict[str, Any] = {
        "initial_rows": len(df),
        "duplicate_rows_removed": 0,
        "invalid_price_rows_removed": 0,
        "missing_customer_ids": 0,
        "cancelled_invoices_count": 0,
        "gross_sales_gbp": 0.0,
        "returns_amount_gbp": 0.0,
        "net_revenue_gbp": 0.0,
        "final_rows": 0,
        "unique_customers": 0,
        "unique_products": 0,
        "date_min": None,
        "date_max": None
    }

    if df.empty:
        return df.copy(), report

    cleaned = df.copy()

    # Standardize column types
    cleaned["Invoice"] = cleaned["Invoice"].astype(str).str.strip()
    cleaned["StockCode"] = cleaned["StockCode"].astype(str).str.strip()
    cleaned["Description"] = cleaned["Description"].fillna("Unknown Item").astype(str).str.strip()
    cleaned["Country"] = cleaned["Country"].fillna("Unknown").astype(str).str.strip()
    
    # Parse InvoiceDate
    cleaned["InvoiceDate"] = pd.to_datetime(cleaned["InvoiceDate"], errors="coerce")
    # Drop rows where date failed to parse
    cleaned = cleaned.dropna(subset=["InvoiceDate"])

    # Convert Quantity and Price to numeric
    cleaned["Quantity"] = pd.to_numeric(cleaned["Quantity"], errors="coerce").fillna(0).astype(int)
    cleaned["Price"] = pd.to_numeric(cleaned["Price"], errors="coerce").fillna(0.0).astype(float)

    # Count missing customer IDs
    null_cust_mask = cleaned["Customer ID"].isna() | (cleaned["Customer ID"].astype(str).str.strip().isin(["", "nan", "None", "null"]))
    report["missing_customer_ids"] = int(null_cust_mask.sum())

    # Detect Cancellations
    cleaned["IsCancelled"] = cleaned["Invoice"].str.upper().str.startswith("C") | (cleaned["Quantity"] < 0)
    report["cancelled_invoices_count"] = int(cleaned["IsCancelled"].sum())

    # Filter out invalid prices (zero or negative prices are adjustments, bad debt, gifts)
    valid_price_mask = cleaned["Price"] > 0
    report["invalid_price_rows_removed"] = int((~valid_price_mask).sum())
    cleaned = cleaned[valid_price_mask].copy()

    # Deduplication
    dedup_cols = ["Invoice", "StockCode", "Quantity", "Price", "InvoiceDate"]
    if "Customer ID" in cleaned.columns:
        dedup_cols.append("Customer ID")
    initial_len = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=dedup_cols, keep="first")
    report["duplicate_rows_removed"] = initial_len - len(cleaned)

    # Standardize Customer ID
    if drop_missing_customers:
        cleaned = cleaned[~cleaned["Customer ID"].isna()].copy()
        # Format Customer ID as integer string (e.g. '13085')
        def format_cust_id(cid):
            try:
                return str(int(float(cid)))
            except (ValueError, TypeError):
                return str(cid).strip()
        cleaned["Customer ID"] = cleaned["Customer ID"].apply(format_cust_id)
        # Drop rows where customer ID is 'nan' or empty
        cleaned = cleaned[~cleaned["Customer ID"].isin(["nan", "", "None", "0"])].copy()
    else:
        cleaned["Customer ID"] = cleaned["Customer ID"].fillna("GUEST").astype(str)

    # Financial line totals
    # For positive quantities (normal sales): LineTotal = Quantity * Price
    # For cancellations/returns: LineTotal = Quantity * Price (negative value)
    cleaned["LineTotal"] = cleaned["Quantity"] * cleaned["Price"]

    # Calculate separated Gross Sales, Returns, and Net Revenue
    sales_mask = (~cleaned["IsCancelled"]) & (cleaned["Quantity"] > 0)
    returns_mask = cleaned["IsCancelled"] | (cleaned["Quantity"] < 0)

    gross_sales = float(cleaned.loc[sales_mask, "LineTotal"].sum())
    returns_amt = float(abs(cleaned.loc[returns_mask, "LineTotal"].sum()))
    net_rev = gross_sales - returns_amt

    report["gross_sales_gbp"] = round(gross_sales, 2)
    report["returns_amount_gbp"] = round(returns_amt, 2)
    report["net_revenue_gbp"] = round(net_rev, 2)
    report["final_rows"] = len(cleaned)
    report["unique_customers"] = int(cleaned["Customer ID"].nunique())
    report["unique_products"] = int(cleaned["StockCode"].nunique())

    if len(cleaned) > 0:
        report["date_min"] = str(cleaned["InvoiceDate"].min())
        report["date_max"] = str(cleaned["InvoiceDate"].max())

    return cleaned, report


def generate_data_health_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate diagnostic metrics for raw data inspection in Data Management.
    """
    total_rows = len(df)
    missing_counts = df.isnull().sum().to_dict()
    missing_pcts = {col: round(cnt / max(total_rows, 1) * 100, 2) for col, cnt in missing_counts.items()}
    
    # Check duplicates
    dup_count = int(df.duplicated().sum())

    # Check cancellations
    inv_col = [c for c in df.columns if str(c).lower().replace(" ", "") in ["invoice", "invoiceno"]]
    cancellations_count = 0
    if inv_col:
        cancellations_count = int(df[inv_col[0]].astype(str).str.upper().str.startswith("C").sum())

    # Check negative quantities
    qty_col = [c for c in df.columns if str(c).lower().replace(" ", "") in ["quantity", "qty"]]
    neg_qty_count = 0
    if qty_col:
        neg_qty_count = int((pd.to_numeric(df[qty_col[0]], errors="coerce") < 0).sum())

    # Check zero/negative price
    price_col = [c for c in df.columns if str(c).lower().replace(" ", "") in ["price", "unitprice"]]
    invalid_price_count = 0
    if price_col:
        invalid_price_count = int((pd.to_numeric(df[price_col[0]], errors="coerce") <= 0).sum())

    return {
        "total_records": total_rows,
        "duplicate_records": dup_count,
        "cancellations_count": cancellations_count,
        "negative_quantity_count": neg_qty_count,
        "invalid_price_count": invalid_price_count,
        "missing_counts": missing_counts,
        "missing_percentages": missing_pcts
    }
