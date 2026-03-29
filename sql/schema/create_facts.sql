CREATE TABLE IF NOT EXISTS fact_sales (
    order_key     INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key      INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key  INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key   INTEGER NOT NULL REFERENCES dim_product(product_key),
    supplier_key  INTEGER NOT NULL REFERENCES dim_supplier(supplier_key),
    quantity      INTEGER NOT NULL,
    unit_price    REAL    NOT NULL,
    discount_pct  REAL    NOT NULL,
    total_amount  REAL    NOT NULL,
    shipping_cost REAL    NOT NULL,
    profit_margin REAL    NOT NULL,
    is_returned   BOOLEAN NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS ix_fact_sales_date_key     ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_customer_key  ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS ix_fact_sales_product_key   ON fact_sales(product_key);

CREATE TABLE IF NOT EXISTS agg_daily_sales (
    id               INTEGER PRIMARY KEY,
    date             DATE    NOT NULL,
    total_revenue    REAL    NOT NULL,
    total_orders     INTEGER NOT NULL,
    avg_order_value  REAL    NOT NULL,
    unique_customers INTEGER NOT NULL
);
