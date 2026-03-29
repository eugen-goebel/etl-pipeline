CREATE TABLE IF NOT EXISTS dim_date (
    date_key      INTEGER PRIMARY KEY,
    full_date     DATE    NOT NULL,
    year          INTEGER NOT NULL,
    quarter       INTEGER NOT NULL,
    month         INTEGER NOT NULL,
    month_name    TEXT    NOT NULL,
    week          INTEGER NOT NULL,
    day_of_week   INTEGER NOT NULL,
    day_name      TEXT    NOT NULL,
    is_weekend    BOOLEAN NOT NULL,
    fiscal_quarter TEXT   NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key  INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL,
    region        TEXT    NOT NULL,
    city          TEXT    NOT NULL,
    segment       TEXT    NOT NULL,
    signup_date   DATE    NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_supplier (
    supplier_key      INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id       TEXT    NOT NULL UNIQUE,
    name              TEXT    NOT NULL,
    country           TEXT    NOT NULL,
    lead_time_days    INTEGER NOT NULL,
    reliability_rating REAL   NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key   INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id    TEXT    NOT NULL UNIQUE,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL,
    subcategory   TEXT    NOT NULL,
    brand         TEXT    NOT NULL,
    supplier_key  INTEGER NOT NULL REFERENCES dim_supplier(supplier_key),
    cost_price    REAL    NOT NULL,
    retail_price  REAL    NOT NULL,
    margin_pct    REAL    NOT NULL
);
