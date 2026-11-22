"""
Cartly Database Management Module
Handles SQLite connection, schema initialization, and database queries.
"""

import os
import sqlite3
from typing import Optional, Dict, Any
import pandas as pd

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database", "cartly.db")
DEFAULT_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "database", "cartly_schema.sql")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Get a connection to the SQLite database with row factory enabled."""
    path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None, schema_path: Optional[str] = None) -> None:
    """Initialize database tables using cartly_schema.sql."""
    db_p = db_path or DEFAULT_DB_PATH
    schema_p = schema_path or DEFAULT_SCHEMA_PATH

    if not os.path.exists(schema_p):
        raise FileNotFoundError(f"Schema file not found at: {schema_p}")

    with open(schema_p, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_connection(db_p) as conn:
        conn.executescript(schema_sql)
        conn.commit()


def execute_query(query: str, params: tuple = (), db_path: Optional[str] = None) -> int:
    """Execute non-SELECT query and return affected rows."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


def fetch_dataframe(query: str, params: tuple = (), db_path: Optional[str] = None) -> pd.DataFrame:
    """Execute SELECT query and return result as a Pandas DataFrame."""
    with get_connection(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def insert_dataframe(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "append",
    db_path: Optional[str] = None
) -> int:
    """Insert or append DataFrame to an SQLite table."""
    with get_connection(db_path) as conn:
        df.to_sql(table_name, conn, if_exists=if_exists, index=False)
        return len(df)


def get_table_counts(db_path: Optional[str] = None) -> Dict[str, int]:
    """Retrieve row counts for each core table."""
    tables = [
        "customers", "products", "orders", "order_items",
        "customer_features", "churn_predictions", "retention_recommendations"
    ]
    counts = {}
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for t in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                counts[t] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                counts[t] = 0
    return counts


def reset_database(db_path: Optional[str] = None) -> None:
    """Drop and recreate all tables."""
    init_db(db_path)
    tables = [
        "retention_recommendations", "churn_predictions", "customer_features",
        "order_items", "orders", "products", "customers"
    ]
    with get_connection(db_path) as conn:
        for t in tables:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        conn.commit()
    init_db(db_path)
