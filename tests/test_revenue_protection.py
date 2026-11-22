"""
Unit tests for Cartly Smart Revenue Protection Engine
"""

import pytest
import pandas as pd
from src.business.revenue_protection import (
    calculate_revenue_at_risk,
    calculate_revenue_protection_summary
)


def test_revenue_at_risk_formula_and_priority():
    # Customer 1: High Spend (£1000 in 180 days), High Risk (0.80) -> Critical Priority
    # Customer 2: Low Spend (£100 in 180 days), Low Risk (0.10) -> Low Priority
    df = pd.DataFrame([
        {
            "customer_id": "C1",
            "monetary_spend": 1000.0,
            "churn_probability": 0.80,
            "risk_tier": "High"
        },
        {
            "customer_id": "C2",
            "monetary_spend": 100.0,
            "churn_probability": 0.10,
            "risk_tier": "Low"
        }
    ])

    res = calculate_revenue_at_risk(df, future_window_days=90, history_window_days=180)

    c1 = res[res["customer_id"] == "C1"].iloc[0]
    c2 = res[res["customer_id"] == "C2"].iloc[0]

    # Future revenue:
    # C1: 1000.0 * (90/180) = 500.00
    # Revenue at risk:
    # C1: 0.80 * 500.00 = 400.00
    assert c1["estimated_future_revenue"] == 500.00
    assert c1["revenue_at_risk"] == 400.00
    assert c1["priority"] == "Critical"

    # C2: 100.0 * 0.5 = 50.00
    # Revenue at risk: 0.10 * 50.00 = 5.00
    assert c2["estimated_future_revenue"] == 50.00
    assert c2["revenue_at_risk"] == 5.00
    assert c2["priority"] == "Low"

    # Ranking: C1 should be rank 1
    assert c1["risk_rank"] == 1
    assert c2["risk_rank"] == 2


def test_revenue_protection_summary():
    df = pd.DataFrame([
        {"customer_id": "1", "estimated_future_revenue": 1000.0, "revenue_at_risk": 500.0, "risk_tier": "High", "customer_value_tier": "High Value", "priority": "Critical"},
        {"customer_id": "2", "estimated_future_revenue": 500.0, "revenue_at_risk": 100.0, "risk_tier": "Low", "customer_value_tier": "Low Value", "priority": "Low"}
    ])

    summary = calculate_revenue_protection_summary(df)

    assert summary["total_revenue_at_risk"] == 600.00
    assert summary["total_future_revenue"] == 1500.00
    assert summary["immediate_attention_customers"] == 1
    assert summary["high_risk_customers"] == 1
