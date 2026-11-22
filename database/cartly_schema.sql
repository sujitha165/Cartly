-- Cartly SQLite Database Schema
-- Retail Intelligence & Revenue Protection System

PRAGMA foreign_keys = ON;

-- 1. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    country TEXT,
    first_purchase_date TEXT,
    last_purchase_date TEXT,
    total_orders INTEGER DEFAULT 0,
    total_spend REAL DEFAULT 0.0,
    rfm_segment TEXT,
    recency_score INTEGER,
    frequency_score INTEGER,
    monetary_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products Table
CREATE TABLE IF NOT EXISTS products (
    stock_code TEXT PRIMARY KEY,
    description TEXT,
    unit_price REAL DEFAULT 0.0,
    total_quantity_sold INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0.0,
    is_active INTEGER DEFAULT 1
);

-- 3. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    invoice_no TEXT PRIMARY KEY,
    customer_id TEXT,
    invoice_date TEXT NOT NULL,
    country TEXT,
    item_count INTEGER DEFAULT 0,
    gross_amount REAL DEFAULT 0.0,
    return_amount REAL DEFAULT 0.0,
    net_amount REAL DEFAULT 0.0,
    is_cancelled INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

-- 4. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_no TEXT NOT NULL,
    stock_code TEXT NOT NULL,
    description TEXT,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL,
    is_cancellation INTEGER DEFAULT 0,
    FOREIGN KEY (invoice_no) REFERENCES orders(invoice_no) ON DELETE CASCADE,
    FOREIGN KEY (stock_code) REFERENCES products(stock_code) ON DELETE CASCADE
);

-- 5. Customer Features Table (Historical Snapshot for ML)
CREATE TABLE IF NOT EXISTS customer_features (
    customer_id TEXT PRIMARY KEY,
    observation_date TEXT NOT NULL,
    recency_days INTEGER NOT NULL,
    frequency_orders INTEGER NOT NULL,
    monetary_spend REAL NOT NULL,
    avg_order_value REAL NOT NULL,
    total_quantity INTEGER NOT NULL,
    cancelled_orders_count INTEGER DEFAULT 0,
    cancellation_rate REAL DEFAULT 0.0,
    distinct_products_count INTEGER DEFAULT 0,
    avg_days_between_purchases REAL DEFAULT 0.0,
    tenure_days INTEGER DEFAULT 0,
    is_churned INTEGER NOT NULL, -- 0 or 1 based on 90-day future window
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 6. Churn Predictions Table
CREATE TABLE IF NOT EXISTS churn_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    churn_probability REAL NOT NULL,
    predicted_churn INTEGER NOT NULL,
    risk_tier TEXT NOT NULL, -- 'High', 'Medium', 'Low'
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- 7. Retention Recommendations Table
CREATE TABLE IF NOT EXISTS retention_recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    customer_value_tier TEXT NOT NULL,
    estimated_future_revenue REAL NOT NULL,
    estimated_revenue_at_risk REAL NOT NULL,
    priority TEXT NOT NULL, -- 'Critical', 'High', 'Medium', 'Low'
    recommended_action TEXT NOT NULL,
    reason TEXT NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(invoice_date);
CREATE INDEX IF NOT EXISTS idx_order_items_invoice ON order_items(invoice_no);
CREATE INDEX IF NOT EXISTS idx_order_items_stock ON order_items(stock_code);
CREATE INDEX IF NOT EXISTS idx_features_churn ON customer_features(is_churned);
CREATE INDEX IF NOT EXISTS idx_predictions_customer ON churn_predictions(customer_id);
CREATE INDEX IF NOT EXISTS idx_predictions_risk ON churn_predictions(risk_tier);
CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON retention_recommendations(priority);
CREATE INDEX IF NOT EXISTS idx_customers_rfm ON customers(rfm_segment);
