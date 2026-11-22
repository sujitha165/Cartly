"""
Cartly Churn Feature Engineering Module
Generates historical customer feature snapshots and operational churn labels
using strict 180-day history and 90-day future prediction windows.
Guarantees NO data leakage and chronological splitting.
"""

from typing import Tuple, Dict, Any, List, Optional
import pandas as pd
import numpy as np


FEATURE_COLUMNS = [
    "recency_days",
    "frequency_orders",
    "monetary_spend",
    "avg_order_value",
    "total_quantity",
    "cancellation_count",
    "cancellation_rate",
    "distinct_products_count",
    "avg_days_between_purchases",
    "tenure_days"
]


def build_churn_snapshot(
    df: pd.DataFrame,
    observation_date: pd.Timestamp,
    history_days: int = 180,
    future_days: int = 90
) -> pd.DataFrame:
    """
    Construct a churn feature dataset for a single observation point in time.
    
    Rules:
    - Features generated strictly from: (observation_date - history_days, observation_date]
    - Churn target evaluated strictly in: (observation_date, observation_date + future_days]
    - Churn Definition: is_churned = 1 if customer makes 0 valid purchases in the future window, else 0.
    """
    obs_dt = pd.to_datetime(observation_date)
    history_start = obs_dt - pd.Timedelta(days=history_days)
    future_end = obs_dt + pd.Timedelta(days=future_days)

    # 1. Historical Slice (Strictly past information)
    hist_mask = (df["InvoiceDate"] > history_start) & (df["InvoiceDate"] <= obs_dt)
    hist_df = df[hist_mask].copy()

    if hist_df.empty:
        return pd.DataFrame()

    # Active customers in historical window
    # Customer must have at least one transaction in the historical window
    cust_groups = hist_df.groupby("Customer ID")

    records = []
    for cust_id, group in cust_groups:
        sales_group = group[(~group["IsCancelled"]) & (group["Quantity"] > 0)]
        returns_group = group[group["IsCancelled"] | (group["Quantity"] < 0)]

        # Frequency: unique valid purchase orders
        freq = sales_group["Invoice"].nunique()
        if freq == 0:
            # If customer only had return/cancellation with no purchases in window, skip or recency is max
            continue

        # Recency: days from last valid purchase to observation date
        last_dt = sales_group["InvoiceDate"].max()
        recency = int((obs_dt - last_dt).total_seconds() // 86400)

        # First purchase in window
        first_dt = sales_group["InvoiceDate"].min()
        tenure = int((obs_dt - first_dt).total_seconds() // 86400)

        # Net Monetary spend in window
        monetary = round(float(group["LineTotal"].sum()), 2)
        # Clip negative spend to 0.01 for feature stability
        monetary = max(monetary, 0.01)

        # Avg Order Value
        aov = round(monetary / max(freq, 1), 2)

        # Total quantity purchased
        total_qty = int(sales_group["Quantity"].sum())

        # Cancellations
        cancel_cnt = len(returns_group)
        cancel_rate = round(cancel_cnt / max(freq + cancel_cnt, 1), 3)

        # Distinct products
        distinct_prods = int(sales_group["StockCode"].nunique())

        # Purchase interval avg
        if freq > 1:
            purchase_dates = sales_group.drop_duplicates("Invoice")["InvoiceDate"].sort_values()
            diffs = purchase_dates.diff().dt.total_seconds().dropna() / 86400.0
            avg_interval = round(float(diffs.mean()), 2)
        else:
            avg_interval = 0.0

        records.append({
            "customer_id": str(cust_id),
            "observation_date": obs_dt.strftime("%Y-%m-%d"),
            "recency_days": max(recency, 0),
            "frequency_orders": int(freq),
            "monetary_spend": monetary,
            "avg_order_value": aov,
            "total_quantity": total_qty,
            "cancellation_count": cancel_cnt,
            "cancellation_rate": cancel_rate,
            "distinct_products_count": distinct_prods,
            "avg_days_between_purchases": avg_interval,
            "tenure_days": max(tenure, 0)
        })

    features_df = pd.DataFrame(records)
    if features_df.empty:
        return pd.DataFrame()

    # 2. Future Slice (Target Label Definition)
    # Check purchases in (observation_date, observation_date + future_days]
    future_mask = (
        (df["InvoiceDate"] > obs_dt) &
        (df["InvoiceDate"] <= future_end) &
        (~df["IsCancelled"]) &
        (df["Quantity"] > 0)
    )
    future_df = df[future_mask]
    future_active_customers = set(future_df["Customer ID"].unique())

    # Churned = 1 if NOT in future_active_customers, else 0
    features_df["is_churned"] = features_df["customer_id"].apply(
        lambda cid: 0 if cid in future_active_customers else 1
    )

    return features_df


def generate_chronological_churn_data(
    df: pd.DataFrame,
    history_days: int = 180,
    future_days: int = 90
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Generate chronological train and test datasets.
    
    If time span is >= 360 days:
      Train snapshot at: max_date - (future_days * 2)
      Test snapshot at: max_date - future_days
    Else:
      Single snapshot at: max_date - future_days, split chronologically by customer tenure/first date.
      
    Returns:
        (train_df, test_df, metadata)
    """
    min_date = df["InvoiceDate"].min()
    max_date = df["InvoiceDate"].max()
    span_days = (max_date - min_date).days

    metadata = {
        "dataset_min_date": str(min_date),
        "dataset_max_date": str(max_date),
        "span_days": span_days,
        "split_method": None,
        "train_obs_date": None,
        "test_obs_date": None
    }

    if span_days >= (history_days + future_days * 2):
        # Two chronological non-overlapping target snapshots
        test_obs = max_date - pd.Timedelta(days=future_days)
        train_obs = test_obs - pd.Timedelta(days=future_days)

        train_snapshot = build_churn_snapshot(df, train_obs, history_days, future_days)
        test_snapshot = build_churn_snapshot(df, test_obs, history_days, future_days)

        metadata["split_method"] = "Chronological Dual-Snapshot"
        metadata["train_obs_date"] = train_obs.strftime("%Y-%m-%d")
        metadata["test_obs_date"] = test_obs.strftime("%Y-%m-%d")

        return train_snapshot, test_snapshot, metadata
    else:
        # Single snapshot with chronological customer cohort split
        obs_date = max_date - pd.Timedelta(days=future_days)
        snapshot = build_churn_snapshot(df, obs_date, history_days, future_days)

        if snapshot.empty:
            return pd.DataFrame(), pd.DataFrame(), metadata

        # Sort chronologically by tenure_days (earliest joined first)
        snapshot = snapshot.sort_values("tenure_days", ascending=False).reset_index(drop=True)
        split_idx = int(len(snapshot) * 0.75)
        train_df = snapshot.iloc[:split_idx].copy()
        test_df = snapshot.iloc[split_idx:].copy()

        metadata["split_method"] = "Chronological Cohort Split (Single Snapshot)"
        metadata["train_obs_date"] = obs_date.strftime("%Y-%m-%d")
        metadata["test_obs_date"] = obs_date.strftime("%Y-%m-%d")

        return train_df, test_df, metadata
