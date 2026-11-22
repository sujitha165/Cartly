"""
Unit tests for Cartly Retention Recommendations Engine
"""

import pytest
import pandas as pd
from src.business.recommendations import (
    generate_customer_recommendation,
    generate_all_recommendations
)


def test_retention_rules_and_fields():
    # Test High Risk + High Value
    row_vip = pd.Series({
        "customer_id": "VIP_101",
        "risk_tier": "High",
        "customer_value_tier": "High Value",
        "revenue_at_risk": 850.50,
        "estimated_future_revenue": 1200.00,
        "recency_days": 110,
        "cancellation_rate": 0.05,
        "priority": "Critical"
    })
    rec_vip = generate_customer_recommendation(row_vip)

    assert "VIP Concierge" in rec_vip["recommended_action"]
    assert rec_vip["customer_id"] == "VIP_101"
    assert rec_vip["risk_level"] == "High"
    assert rec_vip["estimated_revenue_at_risk"] == 850.50
    assert len(rec_vip["reason"]) > 20

    # Test High Risk + Low Value
    row_low = pd.Series({
        "customer_id": "LOW_202",
        "risk_tier": "High",
        "customer_value_tier": "Low Value",
        "revenue_at_risk": 15.00,
        "estimated_future_revenue": 20.00,
        "recency_days": 150,
        "cancellation_rate": 0.0,
        "priority": "Medium"
    })
    rec_low = generate_customer_recommendation(row_low)
    assert "Low-Cost Automated Win-Back" in rec_low["recommended_action"]

    # Test Low Risk + High Value
    row_loyal = pd.Series({
        "customer_id": "LOYAL_303",
        "risk_tier": "Low",
        "customer_value_tier": "High Value",
        "revenue_at_risk": 45.00,
        "estimated_future_revenue": 2500.00,
        "recency_days": 12,
        "cancellation_rate": 0.0,
        "priority": "Low"
    })
    rec_loyal = generate_customer_recommendation(row_loyal)
    assert "Loyalty Expansion" in rec_loyal["recommended_action"]


def test_high_return_rate_trigger():
    row_return = pd.Series({
        "customer_id": "RET_404",
        "risk_tier": "Medium",
        "customer_value_tier": "Medium Value",
        "revenue_at_risk": 120.00,
        "estimated_future_revenue": 300.00,
        "recency_days": 40,
        "cancellation_rate": 0.35,  # 35% return rate
        "priority": "Medium"
    })
    rec_ret = generate_customer_recommendation(row_return)
    assert "Quality Survey" in rec_ret["recommended_action"]
    assert "elevated return" in rec_ret["reason"]


def test_generate_all_recommendations():
    df = pd.DataFrame([
        {"customer_id": "1", "risk_tier": "High", "customer_value_tier": "High Value", "revenue_at_risk": 500.0, "estimated_future_revenue": 800.0, "priority": "Critical"},
        {"customer_id": "2", "risk_tier": "Low", "customer_value_tier": "Low Value", "revenue_at_risk": 10.0, "estimated_future_revenue": 100.0, "priority": "Low"}
    ])

    all_recs = generate_all_recommendations(df)
    assert len(all_recs) == 2
    # Critical should be first
    assert all_recs.iloc[0]["customer_id"] == "1"
    assert all_recs.iloc[0]["priority"] == "Critical"
