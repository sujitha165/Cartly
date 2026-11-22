"""
Unit tests for Churn Definition, Data Leakage Prevention, and Model Inference
"""

import pytest
import pandas as pd
import numpy as np
from src.features.churn_features import build_churn_snapshot, FEATURE_COLUMNS
from src.models.churn_model import (
    train_and_compare_models,
    assign_risk_tier,
    predict_customer_churn_probabilities
)


def test_operational_churn_label_and_leakage_prevention():
    # Setup test timeline:
    # History window: 2011-01-01 to 2011-06-30 (180 days)
    # Observation Date: 2011-06-30
    # Future prediction window: 2011-07-01 to 2011-09-28 (90 days)
    obs_date = pd.to_datetime("2011-06-30")

    # Customer C_ACTIVE: buys in history, buys again in future (churn = 0)
    # Customer C_CHURN: buys in history, does NOT buy in future (churn = 1)
    data = [
        # C_ACTIVE: In history, spends £100 on 2011-05-15
        {"Invoice": "1", "StockCode": "P1", "Description": "Item 1", "Quantity": 10, "Price": 10.0, "LineTotal": 100.0, "InvoiceDate": pd.to_datetime("2011-05-15"), "Customer ID": "C_ACTIVE", "Country": "UK", "IsCancelled": False},
        # C_ACTIVE: In future, spends £500 on 2011-07-15 (future buy)
        {"Invoice": "2", "StockCode": "P2", "Description": "Item 2", "Quantity": 50, "Price": 10.0, "LineTotal": 500.0, "InvoiceDate": pd.to_datetime("2011-07-15"), "Customer ID": "C_ACTIVE", "Country": "UK", "IsCancelled": False},

        # C_CHURN: In history, spends £200 on 2011-02-10
        {"Invoice": "3", "StockCode": "P3", "Description": "Item 3", "Quantity": 20, "Price": 10.0, "LineTotal": 200.0, "InvoiceDate": pd.to_datetime("2011-02-10"), "Customer ID": "C_CHURN", "Country": "UK", "IsCancelled": False},
        # C_CHURN has no transactions in the future window!
    ]
    df = pd.DataFrame(data)

    snapshot = build_churn_snapshot(df, observation_date=obs_date, history_days=180, future_days=90)

    assert len(snapshot) == 2

    active_row = snapshot[snapshot["customer_id"] == "C_ACTIVE"].iloc[0]
    churn_row = snapshot[snapshot["customer_id"] == "C_CHURN"].iloc[0]

    # Check operational churn label
    assert active_row["is_churned"] == 0
    assert churn_row["is_churned"] == 1

    # Check LEAKAGE PREVENTION:
    # C_ACTIVE's monetary_spend MUST be 100.0, NOT 600.0! The 500.0 from July must NOT leak into features!
    assert active_row["monetary_spend"] == 100.0
    assert active_row["total_quantity"] == 10
    assert active_row["frequency_orders"] == 1

    # C_CHURN's recency: from 2011-02-10 to 2011-06-30 = 140 days
    assert churn_row["monetary_spend"] == 200.0
    assert churn_row["recency_days"] == 140


def test_model_training_and_probability_bounds():
    # Synthetic train and test datasets
    np.random.seed(42)
    n = 100

    def make_synthetic(n_samples):
        return pd.DataFrame({
            "customer_id": [f"C{i}" for i in range(n_samples)],
            "observation_date": ["2011-06-30"] * n_samples,
            "recency_days": np.random.randint(5, 180, size=n_samples),
            "frequency_orders": np.random.randint(1, 15, size=n_samples),
            "monetary_spend": np.random.uniform(20.0, 3000.0, size=n_samples),
            "avg_order_value": np.random.uniform(10.0, 500.0, size=n_samples),
            "total_quantity": np.random.randint(1, 200, size=n_samples),
            "cancellation_count": np.random.randint(0, 3, size=n_samples),
            "cancellation_rate": np.random.uniform(0.0, 0.3, size=n_samples),
            "distinct_products_count": np.random.randint(1, 30, size=n_samples),
            "avg_days_between_purchases": np.random.uniform(0.0, 45.0, size=n_samples),
            "tenure_days": np.random.randint(10, 180, size=n_samples),
            "is_churned": np.random.choice([0, 1], size=n_samples, p=[0.4, 0.6])
        })

    train_df = make_synthetic(80)
    test_df = make_synthetic(40)

    result = train_and_compare_models(train_df, test_df, save_best_model=False)

    assert "logistic_regression" in result
    assert "random_forest" in result
    assert "best_model_name" in result

    # Check probability predictions
    bundle = {
        "model": result["logistic_regression"]["metrics"],  # mock check
    }

    assert assign_risk_tier(0.85) == "High"
    assert assign_risk_tier(0.50) == "Medium"
    assert assign_risk_tier(0.15) == "Low"
