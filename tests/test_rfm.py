"""
Unit tests for Cartly RFM Segmentation Module
"""

import pytest
import pandas as pd
import numpy as np
from src.analytics.rfm import (
    calculate_rfm_metrics,
    score_rfm,
    segment_customers,
    get_rfm_segment_summary
)


def test_rfm_metrics_calculation():
    # Customer 1: recent, 2 orders, £300 spend
    # Customer 2: older, 1 order, £50 spend
    ref_dt = pd.to_datetime("2011-03-01")
    data = pd.DataFrame([
        {"Invoice": "1", "StockCode": "P1", "Description": "Item 1", "Quantity": 1, "Price": 100.0, "LineTotal": 100.0, "InvoiceDate": pd.to_datetime("2011-02-25"), "Customer ID": "C1", "Country": "UK", "IsCancelled": False},
        {"Invoice": "2", "StockCode": "P2", "Description": "Item 2", "Quantity": 2, "Price": 100.0, "LineTotal": 200.0, "InvoiceDate": pd.to_datetime("2011-02-28"), "Customer ID": "C1", "Country": "UK", "IsCancelled": False},
        {"Invoice": "3", "StockCode": "P3", "Description": "Item 3", "Quantity": 1, "Price": 50.0, "LineTotal": 50.0, "InvoiceDate": pd.to_datetime("2011-01-01"), "Customer ID": "C2", "Country": "UK", "IsCancelled": False},
    ])

    rfm = calculate_rfm_metrics(data, reference_date=ref_dt)

    c1 = rfm[rfm["CustomerID"] == "C1"].iloc[0]
    c2 = rfm[rfm["CustomerID"] == "C2"].iloc[0]

    assert c1["Frequency"] == 2
    assert c1["Monetary"] == 300.0
    assert c1["Recency"] == 1  # 2011-03-01 minus 2011-02-28 = 1 day

    assert c2["Frequency"] == 1
    assert c2["Monetary"] == 50.0
    assert c2["Recency"] == 59  # 2011-03-01 minus 2011-01-01 = 59 days


def test_rfm_scoring_and_segmentation():
    # Construct synthetic scored RFM frame
    synthetic_scored = pd.DataFrame([
        {"CustomerID": "1", "Recency": 2, "Frequency": 10, "Monetary": 5000.0, "R_Score": 5, "F_Score": 5, "M_Score": 5},
        {"CustomerID": "2", "Recency": 150, "Frequency": 8, "Monetary": 4000.0, "R_Score": 1, "F_Score": 4, "M_Score": 4},
        {"CustomerID": "3", "Recency": 200, "Frequency": 1, "Monetary": 20.0, "R_Score": 1, "F_Score": 1, "M_Score": 1},
    ])

    segmented = segment_customers(synthetic_scored)

    seg1 = segmented[segmented["CustomerID"] == "1"].iloc[0]["Segment"]
    seg2 = segmented[segmented["CustomerID"] == "2"].iloc[0]["Segment"]
    seg3 = segmented[segmented["CustomerID"] == "3"].iloc[0]["Segment"]

    assert seg1 == "Champions"
    assert seg2 == "At Risk"
    assert seg3 == "Hibernating"

    summary = get_rfm_segment_summary(segmented)
    assert len(summary) == 3
    assert "CustomerSharePct" in summary.columns
