"""
Cartly Product Revenue Analysis Module
Calculates product-level revenue, unit volumes, top & bottom performers,
and monthly sales performance trends.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np


def get_product_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue, quantity sold, order count, and returns for each product."""
    if df.empty:
        return pd.DataFrame(columns=[
            "StockCode", "Description", "QuantitySold", "QuantityReturned",
            "GrossRevenue", "ReturnsAmount", "NetRevenue", "OrderCount", "AvgUnitPrice"
        ])

    sales_mask = (~df["IsCancelled"]) & (df["Quantity"] > 0)
    returns_mask = df["IsCancelled"] | (df["Quantity"] < 0)

    # Group by StockCode
    agg = df.groupby("StockCode").agg(
        Description=("Description", "first"),
        QuantitySold=("Quantity", lambda s: int(s[s > 0].sum())),
        QuantityReturned=("Quantity", lambda s: int(abs(s[s < 0].sum()))),
        GrossRevenue=("LineTotal", lambda s: float(s[s > 0].sum())),
        ReturnsAmount=("LineTotal", lambda s: float(abs(s[s < 0].sum()))),
        NetRevenue=("LineTotal", "sum"),
        OrderCount=("Invoice", "nunique"),
        AvgUnitPrice=("Price", "mean")
    ).reset_index()

    agg["GrossRevenue"] = agg["GrossRevenue"].round(2)
    agg["ReturnsAmount"] = agg["ReturnsAmount"].round(2)
    agg["NetRevenue"] = agg["NetRevenue"].round(2)
    agg["AvgUnitPrice"] = agg["AvgUnitPrice"].round(2)

    return agg.sort_values("NetRevenue", ascending=False).reset_index(drop=True)


def get_top_products(df: pd.DataFrame, top_n: int = 10, metric: str = "NetRevenue") -> pd.DataFrame:
    """Return top N products ranked by specified metric ('NetRevenue' or 'QuantitySold')."""
    summary = get_product_summary(df)
    if metric not in summary.columns:
        metric = "NetRevenue"
    return summary.sort_values(metric, ascending=False).head(top_n).reset_index(drop=True)


def get_lowest_performing_products(
    df: pd.DataFrame,
    bottom_n: int = 10,
    min_orders: int = 1
) -> pd.DataFrame:
    """
    Return lowest-performing products (with at least min_orders) to identify
    underperforming or high-return inventory items.
    """
    summary = get_product_summary(df)
    filtered = summary[summary["OrderCount"] >= min_orders]
    return filtered.sort_values("NetRevenue", ascending=True).head(bottom_n).reset_index(drop=True)


def get_product_monthly_trend(
    df: pd.DataFrame,
    stock_codes: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Compute monthly revenue trajectory for specific products or top 5 products if none specified.
    """
    if df.empty:
        return pd.DataFrame(columns=["YearMonth", "StockCode", "Description", "MonthlyRevenue", "MonthlyQuantity"])

    temp = df.copy()
    temp["YearMonth"] = temp["InvoiceDate"].dt.to_period("M").astype(str)

    if not stock_codes:
        # Default to top 5 products by NetRevenue
        top5 = get_top_products(temp, top_n=5)["StockCode"].tolist()
        stock_codes = top5

    temp = temp[temp["StockCode"].isin(stock_codes)]

    monthly = temp.groupby(["YearMonth", "StockCode"]).agg(
        Description=("Description", "first"),
        MonthlyRevenue=("LineTotal", "sum"),
        MonthlyQuantity=("Quantity", lambda s: int(s[s > 0].sum()))
    ).reset_index()

    monthly["MonthlyRevenue"] = monthly["MonthlyRevenue"].round(2)
    return monthly.sort_values(["YearMonth", "MonthlyRevenue"], ascending=[True, False]).reset_index(drop=True)
