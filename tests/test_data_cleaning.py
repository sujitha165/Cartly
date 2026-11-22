"""
Unit tests for Cartly Data Cleaning and Quality Module
"""

import pytest
import pandas as pd
import numpy as np
from src.data.cleaner import clean_retail_data, generate_data_health_report
from src.data.loader import normalize_column_names, validate_columns


def test_column_normalization_and_validation():
    raw_df = pd.DataFrame({
        "invoice_no": ["1001"],
        "stock_code": ["85123A"],
        "item_name": ["White Hanging Heart T-Light"],
        "qty": [6],
        "invoice_date": ["2010-12-01 08:26:00"],
        "unit_price": [2.55],
        "customer_id": ["17850"],
        "country": ["United Kingdom"]
    })

    norm_df = normalize_column_names(raw_df)
    is_valid, present, missing = validate_columns(norm_df)

    assert is_valid is True
    assert len(missing) == 0
    assert "Invoice" in norm_df.columns
    assert "StockCode" in norm_df.columns
    assert "Customer ID" in norm_df.columns


def test_clean_retail_data_cancellations_and_returns():
    # Synthetic transactions with regular sales, returns, and cancellations
    sample_data = pd.DataFrame({
        "Invoice": ["536365", "C536379", "536366", "536367", "536365"],  # One duplicate row
        "StockCode": ["85123A", "D", "22633", "84879", "85123A"],
        "Description": ["Product A", "Discount", "Product B", "Product C", "Product A"],
        "Quantity": [10, -1, 5, 2, 10],
        "InvoiceDate": [
            "2010-12-01 08:26:00",
            "2010-12-01 09:41:00",
            "2010-12-01 08:28:00",
            "2010-12-01 08:34:00",
            "2010-12-01 08:26:00"  # Duplicate
        ],
        "Price": [2.50, 10.00, 4.00, 0.00, 2.50],  # One invalid price (0.00)
        "Customer ID": ["17850", "14527", "17850", "13047", "17850"],
        "Country": ["United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom"]
    })

    cleaned_df, report = clean_retail_data(sample_data, drop_missing_customers=True)

    # Invoices:
    # 536365: Qty 10 * 2.50 = 25.00 (Valid Sale)
    # C536379: Qty -1 * 10.00 = -10.00 (Cancellation/Return)
    # 536366: Qty 5 * 4.00 = 20.00 (Valid Sale)
    # 536367: Price 0.00 -> Dropped as invalid price
    # Duplicate row dropped

    assert report["duplicate_rows_removed"] == 1
    assert report["invalid_price_rows_removed"] == 1
    assert report["gross_sales_gbp"] == 45.00  # 25.00 + 20.00
    assert report["returns_amount_gbp"] == 10.00
    assert report["net_revenue_gbp"] == 35.00  # 45.00 - 10.00


def test_missing_customer_id_handling():
    data = pd.DataFrame({
        "Invoice": ["1001", "1002"],
        "StockCode": ["A1", "A2"],
        "Description": ["Item 1", "Item 2"],
        "Quantity": [2, 3],
        "InvoiceDate": ["2010-12-01", "2010-12-02"],
        "Price": [10.0, 5.0],
        "Customer ID": [None, "12345"],
        "Country": ["UK", "UK"]
    })

    cleaned_with_drop, report = clean_retail_data(data, drop_missing_customers=True)
    assert len(cleaned_with_drop) == 1
    assert report["missing_customer_ids"] == 1

    cleaned_without_drop, _ = clean_retail_data(data, drop_missing_customers=False)
    assert len(cleaned_without_drop) == 2
    assert "GUEST" in cleaned_without_drop["Customer ID"].values
