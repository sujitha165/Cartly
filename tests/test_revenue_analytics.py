"""
Unit tests for Cartly Revenue and Product Analytics Modules
"""

import pytest
import pandas as pd
from src.analytics.executive import (
    calculate_executive_kpis,
    calculate_monthly_revenue_trends,
    calculate_top_selling_products
)
from src.analytics.product_analytics import (
    get_product_summary,
    get_top_products,
    get_lowest_performing_products
)


@pytest.fixture
def sample_cleaned_df():
    data = [
        # Customer 101, Jan 2011, Sale £100
        {"Invoice": "101", "StockCode": "P1", "Description": "Prod 1", "Quantity": 10, "Price": 10.0, "LineTotal": 100.0, "InvoiceDate": pd.to_datetime("2011-01-10"), "Customer ID": "101", "Country": "UK", "IsCancelled": False},
        # Customer 101, Jan 2011, Sale £50
        {"Invoice": "102", "StockCode": "P2", "Description": "Prod 2", "Quantity": 5, "Price": 10.0, "LineTotal": 50.0, "InvoiceDate": pd.to_datetime("2011-01-15"), "Customer ID": "101", "Country": "UK", "IsCancelled": False},
        # Customer 102, Jan 2011, Return £20
        {"Invoice": "C103", "StockCode": "P1", "Description": "Prod 1", "Quantity": -2, "Price": 10.0, "LineTotal": -20.0, "InvoiceDate": pd.to_datetime("2011-01-20"), "Customer ID": "102", "Country": "UK", "IsCancelled": True},
        # Customer 103, Feb 2011, Sale £200
        {"Invoice": "104", "StockCode": "P3", "Description": "Prod 3", "Quantity": 20, "Price": 10.0, "LineTotal": 200.0, "InvoiceDate": pd.to_datetime("2011-02-05"), "Customer ID": "103", "Country": "France", "IsCancelled": False},
    ]
    return pd.DataFrame(data)


def test_executive_kpi_calculations(sample_cleaned_df):
    kpis = calculate_executive_kpis(sample_cleaned_df)

    # Gross: 100 + 50 + 200 = 350.00
    # Returns: 20.00
    # Net: 350 - 20 = 330.00
    # Orders (valid sales): 3 (101, 102, 104)
    # Customers: 3 (101, 102, 103)
    # Products: 3 (P1, P2, P3)
    # AOV: 330 / 3 = 110.00

    assert kpis["gross_revenue"] == 350.00
    assert kpis["return_amount"] == 20.00
    assert kpis["net_revenue"] == 330.00
    assert kpis["total_orders"] == 3
    assert kpis["total_customers"] == 3
    assert kpis["total_products"] == 3
    assert kpis["average_order_value"] == 110.00


def test_monthly_trends(sample_cleaned_df):
    trends = calculate_monthly_revenue_trends(sample_cleaned_df)
    assert len(trends) == 2  # 2011-01 and 2011-02

    jan = trends[trends["YearMonth"] == "2011-01"].iloc[0]
    assert jan["GrossSales"] == 150.00
    assert jan["Returns"] == 20.00
    assert jan["NetRevenue"] == 130.00

    feb = trends[trends["YearMonth"] == "2011-02"].iloc[0]
    assert feb["NetRevenue"] == 200.00


def test_product_summary_and_top_ranking(sample_cleaned_df):
    prod_sum = get_product_summary(sample_cleaned_df)
    assert len(prod_sum) == 3

    top = get_top_products(sample_cleaned_df, top_n=1)
    # P3 has 200 Net Revenue, P1 has 80 (100 - 20), P2 has 50
    assert top.iloc[0]["StockCode"] == "P3"
    assert top.iloc[0]["NetRevenue"] == 200.00

    bottom = get_lowest_performing_products(sample_cleaned_df, bottom_n=1)
    assert bottom.iloc[0]["StockCode"] == "P2"
    assert bottom.iloc[0]["NetRevenue"] == 50.00
