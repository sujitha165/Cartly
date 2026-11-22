"""
Cartly Smart Revenue Protection Engine
Signature Feature: Quantifies customer financial value, computes expected future revenue,
evaluates estimated revenue at risk, and assigns action priorities.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd


def calculate_revenue_at_risk(
    predicted_df: pd.DataFrame,
    future_window_days: int = 90,
    history_window_days: int = 180
) -> pd.DataFrame:
    """
    Apply Cartly's baseline revenue protection formula:
    
    Estimated Future Revenue = (Historical Spend in Window / History Days) * Future Days
    Estimated Revenue at Risk = Churn Probability * Estimated Future Revenue
    
    Customers are categorized into Value Tiers and Action Priorities.
    """
    if predicted_df.empty:
        return pd.DataFrame()

    df = predicted_df.copy()

    # 1. Estimate Future Revenue based on historical run-rate
    # If monetary_spend is available from feature engineering:
    if "monetary_spend" in df.columns:
        spend_col = "monetary_spend"
    elif "Monetary" in df.columns:
        spend_col = "Monetary"
    elif "total_spend" in df.columns:
        spend_col = "total_spend"
    else:
        spend_col = None

    if spend_col:
        # Annualized / windowed run-rate
        run_rate_factor = future_window_days / float(history_window_days)
        df["estimated_future_revenue"] = (df[spend_col].clip(lower=0.0) * run_rate_factor).round(2)
    else:
        df["estimated_future_revenue"] = 0.0

    # Ensure churn probability exists
    if "churn_probability" not in df.columns:
        df["churn_probability"] = 0.5

    # 2. Signature Revenue at Risk Formula
    df["revenue_at_risk"] = (df["churn_probability"] * df["estimated_future_revenue"]).round(2)

    # 3. Categorize Customer Value Tier (High, Medium, Low based on quantiles or absolute bounds)
    val_75 = df["estimated_future_revenue"].quantile(0.75)
    val_25 = df["estimated_future_revenue"].quantile(0.25)

    def assign_value_tier(rev):
        if rev >= val_75 and rev > 0:
            return "High Value"
        elif rev >= val_25:
            return "Medium Value"
        else:
            return "Low Value"

    df["customer_value_tier"] = df["estimated_future_revenue"].apply(assign_value_tier)

    # Ensure risk_tier exists
    if "risk_tier" not in df.columns:
        def r_tier(p):
            return "High" if p >= 0.70 else ("Medium" if p >= 0.35 else "Low")
        df["risk_tier"] = df["churn_probability"].apply(r_tier)

    # 4. Action Priority Assignment
    def assign_priority(row):
        r = row["risk_tier"]
        v = row["customer_value_tier"]

        if r == "High" and v == "High Value":
            return "Critical"
        elif (r == "High" and v == "Medium Value") or (r == "Medium" and v == "High Value"):
            return "High"
        elif (r == "Medium" and v == "Medium Value") or (r == "High" and v == "Low Value"):
            return "Medium"
        else:
            return "Low"

    df["priority"] = df.apply(assign_priority, axis=1)

    # 5. Rank customers by Revenue at Risk descending
    df = df.sort_values("revenue_at_risk", ascending=False).reset_index(drop=True)
    df["risk_rank"] = df.index + 1

    return df


def calculate_revenue_protection_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate executive level revenue at risk metrics."""
    if df.empty or "revenue_at_risk" not in df.columns:
        return {
            "total_revenue_at_risk": 0.0,
            "total_future_revenue": 0.0,
            "pct_revenue_at_risk": 0.0,
            "high_risk_customers": 0,
            "high_value_customers": 0,
            "immediate_attention_customers": 0,
            "avg_revenue_at_risk_per_customer": 0.0
        }

    total_risk = float(df["revenue_at_risk"].sum())
    total_future = float(df["estimated_future_revenue"].sum())
    pct_risk = round((total_risk / max(total_future, 0.01)) * 100, 1)

    high_risk_cnt = int((df["risk_tier"] == "High").sum())
    high_val_cnt = int((df["customer_value_tier"] == "High Value").sum())
    immediate_cnt = int((df["priority"] == "Critical").sum())
    avg_risk = round(total_risk / max(len(df), 1), 2)

    return {
        "total_revenue_at_risk": round(total_risk, 2),
        "total_future_revenue": round(total_future, 2),
        "pct_revenue_at_risk": pct_risk,
        "high_risk_customers": high_risk_cnt,
        "high_value_customers": high_val_cnt,
        "immediate_attention_customers": immediate_cnt,
        "avg_revenue_at_risk_per_customer": avg_risk
    }
