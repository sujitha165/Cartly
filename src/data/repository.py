"""
Cartly Database Repository Module
Coordinates ingesting cleaned retail data into SQLite tables
(customers, products, orders, order_items) with relational integrity.
"""

from typing import Optional, Dict, Any
import sqlite3
import pandas as pd
from .db import get_connection, init_db


def sync_cleaned_data_to_db(
    cleaned_df: pd.DataFrame,
    db_path: Optional[str] = None,
    batch_size: int = 10000
) -> Dict[str, int]:
    """
    Transform and insert cleaned transactions into relational SQLite tables:
    customers, products, orders, order_items.
    """
    init_db(db_path)
    if cleaned_df.empty:
        return {"customers": 0, "products": 0, "orders": 0, "order_items": 0}

    df = cleaned_df.copy()
    df["InvoiceDateStr"] = pd.to_datetime(df["InvoiceDate"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    # 1. Aggregate Products
    # Net sales and total quantity
    prod_agg = df.groupby("StockCode").agg(
        description=("Description", "first"),
        unit_price=("Price", "mean"),
        total_quantity_sold=("Quantity", lambda s: int(s[s > 0].sum())),
        total_revenue=("LineTotal", "sum")
    ).reset_index()
    prod_agg["unit_price"] = prod_agg["unit_price"].round(2)
    prod_agg["total_revenue"] = prod_agg["total_revenue"].round(2)
    prod_agg["is_active"] = 1
    prod_agg = prod_agg.rename(columns={
        "StockCode": "stock_code",
        "total_quantity_sold": "total_quantity_sold",
        "total_revenue": "total_revenue"
    })

    # 2. Aggregate Orders
    order_agg = df.groupby(["Invoice", "Customer ID", "InvoiceDateStr", "Country", "IsCancelled"]).agg(
        item_count=("StockCode", "count"),
        gross_amount=("LineTotal", lambda s: float(s[s > 0].sum())),
        return_amount=("LineTotal", lambda s: float(abs(s[s < 0].sum()))),
        net_amount=("LineTotal", "sum")
    ).reset_index()

    order_agg["gross_amount"] = order_agg["gross_amount"].round(2)
    order_agg["return_amount"] = order_agg["return_amount"].round(2)
    order_agg["net_amount"] = order_agg["net_amount"].round(2)
    order_agg["is_cancelled"] = order_agg["IsCancelled"].astype(int)

    order_agg = order_agg.rename(columns={
        "Invoice": "invoice_no",
        "Customer ID": "customer_id",
        "InvoiceDateStr": "invoice_date",
        "Country": "country",
        "item_count": "item_count",
    })
    orders_table_df = order_agg[[
        "invoice_no", "customer_id", "invoice_date", "country",
        "item_count", "gross_amount", "return_amount", "net_amount", "is_cancelled"
    ]]

    # 3. Aggregate Customers
    cust_agg = df.groupby("Customer ID").agg(
        country=("Country", "first"),
        first_purchase_date=("InvoiceDateStr", "min"),
        last_purchase_date=("InvoiceDateStr", "max"),
        total_orders=("Invoice", "nunique"),
        total_spend=("LineTotal", "sum")
    ).reset_index()

    cust_agg["total_spend"] = cust_agg["total_spend"].round(2)
    cust_agg = cust_agg.rename(columns={"Customer ID": "customer_id"})
    cust_agg["rfm_segment"] = None
    cust_agg["recency_score"] = None
    cust_agg["frequency_score"] = None
    cust_agg["monetary_score"] = None

    # 4. Prepare Order Items
    order_items_df = pd.DataFrame({
        "invoice_no": df["Invoice"].astype(str),
        "stock_code": df["StockCode"].astype(str),
        "description": df["Description"].astype(str),
        "quantity": df["Quantity"].astype(int),
        "unit_price": df["Price"].astype(float).round(2),
        "line_total": df["LineTotal"].astype(float).round(2),
        "is_cancellation": df["IsCancelled"].astype(int)
    })

    # Write to SQLite using transactions
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Temporary disable foreign keys for bulk insert
        cursor.execute("PRAGMA foreign_keys = OFF;")

        # Insert / Replace Customers
        cust_agg.to_sql("customers", conn, if_exists="replace", index=False)

        # Insert / Replace Products
        prod_agg.to_sql("products", conn, if_exists="replace", index=False)

        # Insert / Replace Orders
        orders_table_df.to_sql("orders", conn, if_exists="replace", index=False)

        # Insert / Replace Order Items
        order_items_df.to_sql("order_items", conn, if_exists="replace", index=False)

        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()

    return {
        "customers": len(cust_agg),
        "products": len(prod_agg),
        "orders": len(orders_table_df),
        "order_items": len(order_items_df)
    }


def sync_features_to_db(features_df: pd.DataFrame, db_path: Optional[str] = None) -> int:
    """Store computed customer ML features in customer_features table."""
    if features_df.empty:
        return 0
    cols = [
        "customer_id", "observation_date", "recency_days", "frequency_orders",
        "monetary_spend", "avg_order_value", "total_quantity", "cancellation_count",
        "cancellation_rate", "distinct_products_count", "avg_days_between_purchases",
        "tenure_days", "is_churned"
    ]
    avail_cols = [c for c in cols if c in features_df.columns]
    subset = features_df[avail_cols].copy()
    with get_connection(db_path) as conn:
        subset.to_sql("customer_features", conn, if_exists="replace", index=False)
    return len(subset)


def sync_predictions_to_db(predictions_df: pd.DataFrame, model_name: str = "Random Forest", db_path: Optional[str] = None) -> int:
    """Store customer churn predictions in churn_predictions table."""
    if predictions_df.empty:
        return 0
    save_df = pd.DataFrame({
        "customer_id": predictions_df["customer_id"].astype(str),
        "model_name": model_name,
        "churn_probability": predictions_df["churn_probability"].astype(float),
        "predicted_churn": predictions_df["predicted_churn"].astype(int),
        "risk_tier": predictions_df["risk_tier"].astype(str)
    })
    with get_connection(db_path) as conn:
        save_df.to_sql("churn_predictions", conn, if_exists="replace", index=False)
    return len(save_df)


def sync_recommendations_to_db(recommendations_df: pd.DataFrame, db_path: Optional[str] = None) -> int:
    """Store retention recommendations in retention_recommendations table."""
    if recommendations_df.empty:
        return 0
    cols = [
        "customer_id", "risk_level", "customer_value_tier", "estimated_future_revenue",
        "estimated_revenue_at_risk", "priority", "recommended_action", "reason"
    ]
    avail = [c for c in cols if c in recommendations_df.columns]
    subset = recommendations_df[avail].copy()
    with get_connection(db_path) as conn:
        subset.to_sql("retention_recommendations", conn, if_exists="replace", index=False)
    return len(subset)
