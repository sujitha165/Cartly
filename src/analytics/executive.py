"""
Cartly Executive Analytics Module
Computes high-level retail KPIs, monthly revenue trends, customer purchasing trends,
and top-selling products with support for date and country filtering.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np


def filter_transactions(
    df: pd.DataFrame,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
    countries: Optional[List[str]] = None
) -> pd.DataFrame:
    """Filter DataFrame by date range and countries."""
    if df.empty:
        return df

    filtered = df.copy()

    if start_date is not None:
        filtered = filtered[filtered["InvoiceDate"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["InvoiceDate"] <= pd.to_datetime(end_date)]
    if countries and len(countries) > 0 and "All" not in countries:
        filtered = filtered[filtered["Country"].isin(countries)]

    return filtered


def calculate_executive_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate executive level KPIs with financial accuracy."""
    if df.empty:
        return {
            "net_revenue": 0.0,
            "gross_revenue": 0.0,
            "return_amount": 0.0,
            "return_rate_pct": 0.0,
            "total_orders": 0,
            "total_customers": 0,
            "total_products": 0,
            "average_order_value": 0.0,
            "average_items_per_order": 0.0
        }

    sales_mask = (~df["IsCancelled"]) & (df["Quantity"] > 0)
    returns_mask = df["IsCancelled"] | (df["Quantity"] < 0)

    gross_rev = float(df.loc[sales_mask, "LineTotal"].sum())
    returns_amt = float(abs(df.loc[returns_mask, "LineTotal"].sum()))
    net_rev = gross_rev - returns_amt

    total_orders = int(df.loc[sales_mask, "Invoice"].nunique())
    total_customers = int(df["Customer ID"].nunique())
    total_products = int(df["StockCode"].nunique())

    aov = (net_rev / total_orders) if total_orders > 0 else 0.0
    return_rate_pct = (returns_amt / gross_rev * 100) if gross_rev > 0 else 0.0

    items_per_order = float(df.loc[sales_mask, "Quantity"].sum() / total_orders) if total_orders > 0 else 0.0

    return {
        "net_revenue": round(net_rev, 2),
        "gross_revenue": round(gross_rev, 2),
        "return_amount": round(returns_amt, 2),
        "return_rate_pct": round(return_rate_pct, 2),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "total_products": total_products,
        "average_order_value": round(aov, 2),
        "average_items_per_order": round(items_per_order, 1)
    }


def calculate_monthly_revenue_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate monthly breakdown of gross sales, returns, net revenue, and order volume."""
    if df.empty:
        return pd.DataFrame(columns=["YearMonth", "GrossSales", "Returns", "NetRevenue", "Orders", "ActiveCustomers"])

    temp = df.copy()
    temp["YearMonth"] = temp["InvoiceDate"].dt.to_period("M").astype(str)

    monthly_list = []
    for ym, group in temp.groupby("YearMonth"):
        sales_mask = (~group["IsCancelled"]) & (group["Quantity"] > 0)
        returns_mask = group["IsCancelled"] | (group["Quantity"] < 0)

        gross = float(group.loc[sales_mask, "LineTotal"].sum())
        ret = float(abs(group.loc[returns_mask, "LineTotal"].sum()))
        net = gross - ret
        orders = int(group.loc[sales_mask, "Invoice"].nunique())
        customers = int(group["Customer ID"].nunique())

        monthly_list.append({
            "YearMonth": ym,
            "GrossSales": round(gross, 2),
            "Returns": round(ret, 2),
            "NetRevenue": round(net, 2),
            "Orders": orders,
            "ActiveCustomers": customers
        })

    return pd.DataFrame(monthly_list).sort_values("YearMonth").reset_index(drop=True)


def calculate_top_selling_products(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Compute top-performing products by net revenue."""
    if df.empty:
        return pd.DataFrame(columns=["StockCode", "Description", "TotalQuantity", "NetRevenue"])

    agg = df.groupby("StockCode").agg(
        Description=("Description", "first"),
        TotalQuantity=("Quantity", lambda s: int(s[s > 0].sum())),
        NetRevenue=("LineTotal", "sum")
    ).reset_index()

    agg["NetRevenue"] = agg["NetRevenue"].round(2)
    return agg.sort_values("NetRevenue", ascending=False).head(top_n).reset_index(drop=True)


def calculate_customer_purchasing_trends(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze monthly customer retention trends and active customer growth."""
    if df.empty:
        return pd.DataFrame(columns=["YearMonth", "TotalActive", "AvgSpendPerCustomer"])

    temp = df.copy()
    temp["YearMonth"] = temp["InvoiceDate"].dt.to_period("M").astype(str)

    res = temp.groupby("YearMonth").agg(
        TotalActive=("Customer ID", "nunique"),
        NetRevenue=("LineTotal", "sum")
    ).reset_index()

    res["AvgSpendPerCustomer"] = (res["NetRevenue"] / res["TotalActive"]).round(2)
    return res.sort_values("YearMonth").reset_index(drop=True)
