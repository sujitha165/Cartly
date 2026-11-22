"""
Unit and Integration tests for Cartly SQLite Database persistence
"""

import os
import pytest
import pandas as pd
from src.data.db import init_db, get_connection, get_table_counts, reset_database
from src.data.repository import (
    sync_cleaned_data_to_db,
    sync_features_to_db,
    sync_predictions_to_db,
    sync_recommendations_to_db
)


@pytest.fixture
def temp_db(tmp_path):
    db_file = str(tmp_path / "test_cartly.db")
    schema_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "cartly_schema.sql")
    init_db(db_path=db_file, schema_path=schema_file)
    return db_file


def test_sqlite_table_initialization_and_sync(temp_db):
    counts = get_table_counts(temp_db)
    for table in ["customers", "products", "orders", "order_items", "customer_features", "churn_predictions", "retention_recommendations"]:
        assert table in counts
        assert counts[table] == 0

    # Sync sample cleaned data
    sample_df = pd.DataFrame([
        {
            "Invoice": "50001",
            "StockCode": "SKU1",
            "Description": "Test Product",
            "Quantity": 5,
            "Price": 20.0,
            "LineTotal": 100.0,
            "InvoiceDate": pd.to_datetime("2011-05-01 10:00:00"),
            "Customer ID": "CUST100",
            "Country": "United Kingdom",
            "IsCancelled": False
        }
    ])

    sync_res = sync_cleaned_data_to_db(sample_df, db_path=temp_db)
    assert sync_res["customers"] == 1
    assert sync_res["products"] == 1
    assert sync_res["orders"] == 1
    assert sync_res["order_items"] == 1

    # Sync features
    feats_df = pd.DataFrame([{
        "customer_id": "CUST100",
        "observation_date": "2011-06-01",
        "recency_days": 31,
        "frequency_orders": 1,
        "monetary_spend": 100.0,
        "avg_order_value": 100.0,
        "total_quantity": 5,
        "cancellation_count": 0,
        "cancellation_rate": 0.0,
        "distinct_products_count": 1,
        "avg_days_between_purchases": 0.0,
        "tenure_days": 31,
        "is_churned": 0
    }])
    n_feats = sync_features_to_db(feats_df, db_path=temp_db)
    assert n_feats == 1

    # Sync predictions
    preds_df = pd.DataFrame([{
        "customer_id": "CUST100",
        "churn_probability": 0.25,
        "predicted_churn": 0,
        "risk_tier": "Low"
    }])
    n_preds = sync_predictions_to_db(preds_df, model_name="Random Forest", db_path=temp_db)
    assert n_preds == 1

    # Sync recommendations
    recs_df = pd.DataFrame([{
        "customer_id": "CUST100",
        "risk_level": "Low",
        "customer_value_tier": "High Value",
        "estimated_future_revenue": 50.0,
        "estimated_revenue_at_risk": 12.5,
        "priority": "Low",
        "recommended_action": "Loyalty Expansion",
        "reason": "Stable VIP account."
    }])
    n_recs = sync_recommendations_to_db(recs_df, db_path=temp_db)
    assert n_recs == 1

    final_counts = get_table_counts(temp_db)
    assert final_counts["customers"] == 1
    assert final_counts["products"] == 1
    assert final_counts["orders"] == 1
    assert final_counts["order_items"] == 1
    assert final_counts["customer_features"] == 1
    assert final_counts["churn_predictions"] == 1
    assert final_counts["retention_recommendations"] == 1
