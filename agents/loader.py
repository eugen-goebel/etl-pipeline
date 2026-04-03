"""Database loader -- idempotent load of star schema into SQLite."""

import os
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from db.database import Base, get_engine
from db.orm_models import (DimDateTable, DimCustomerTable, DimSupplierTable,
                           DimProductTable, FactSalesTable, AggDailySalesTable,
                           DataQualityIssueTable, LoadMetadataTable)


class DatabaseLoader:

    def __init__(self, db_path: str = "output/shopflow.db"):
        self.engine = get_engine(db_path)
        self.db_path = db_path

    def initialize(self):
        """Create all tables (idempotent)."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        Base.metadata.create_all(self.engine)

    def get_last_load(self, table_name: str) -> str | None:
        """Return the last load timestamp for a given table, or None."""
        with self.engine.connect() as conn:
            row = conn.execute(
                text("SELECT last_load_at FROM load_metadata WHERE table_name = :t"),
                {"t": table_name},
            ).fetchone()
        return row[0] if row else None

    def _update_metadata(self, conn, table_name: str, records: int, mode: str):
        """Upsert load metadata for a table."""
        now = datetime.now(timezone.utc).isoformat()
        existing = conn.execute(
            text("SELECT id FROM load_metadata WHERE table_name = :t"),
            {"t": table_name},
        ).fetchone()
        if existing:
            conn.execute(
                text(
                    "UPDATE load_metadata SET last_load_at = :ts, "
                    "records_processed = :r, load_mode = :m WHERE table_name = :t"
                ),
                {"ts": now, "r": records, "m": mode, "t": table_name},
            )
        else:
            conn.execute(
                text(
                    "INSERT INTO load_metadata (table_name, last_load_at, records_processed, load_mode) "
                    "VALUES (:t, :ts, :r, :m)"
                ),
                {"t": table_name, "ts": now, "r": records, "m": mode},
            )

    def load(self, dim_date: pd.DataFrame, dim_customer: pd.DataFrame, dim_product: pd.DataFrame,
             dim_supplier: pd.DataFrame, fact_sales: pd.DataFrame, quality_issues: pd.DataFrame | None = None):
        """Full refresh load -- replace all table contents within a transaction."""
        self.initialize()

        with self.engine.begin() as conn:
            # Clear existing data (order matters for FK constraints)
            conn.execute(text("DELETE FROM agg_daily_sales"))
            conn.execute(text("DELETE FROM fact_sales"))
            conn.execute(text("DELETE FROM dim_product"))
            conn.execute(text("DELETE FROM dim_customer"))
            conn.execute(text("DELETE FROM dim_supplier"))
            conn.execute(text("DELETE FROM dim_date"))
            if quality_issues is not None:
                conn.execute(text("DELETE FROM data_quality_issues"))

        # Load dimensions first, then facts
        dim_date.to_sql("dim_date", self.engine, if_exists="append", index=False)
        dim_supplier.to_sql("dim_supplier", self.engine, if_exists="append", index=False)
        dim_customer.to_sql("dim_customer", self.engine, if_exists="append", index=False)
        dim_product.to_sql("dim_product", self.engine, if_exists="append", index=False)
        fact_sales.to_sql("fact_sales", self.engine, if_exists="append", index=False)

        if quality_issues is not None and len(quality_issues) > 0:
            quality_issues.to_sql("data_quality_issues", self.engine, if_exists="append", index=False)

        # Update metadata for each table
        with self.engine.begin() as conn:
            self._update_metadata(conn, "dim_date", len(dim_date), "full")
            self._update_metadata(conn, "dim_customer", len(dim_customer), "full")
            self._update_metadata(conn, "dim_supplier", len(dim_supplier), "full")
            self._update_metadata(conn, "dim_product", len(dim_product), "full")
            self._update_metadata(conn, "fact_sales", len(fact_sales), "full")

        # Build aggregates
        self._build_aggregates()

    def load_incremental(self, dim_date: pd.DataFrame, dim_customer: pd.DataFrame,
                         dim_product: pd.DataFrame, dim_supplier: pd.DataFrame,
                         fact_sales: pd.DataFrame, quality_issues: pd.DataFrame | None = None):
        """Incremental load -- upsert dimensions and append new facts."""
        self.initialize()

        # If no prior load exists, fall back to full load
        if self.get_last_load("fact_sales") is None:
            print("      no prior load found, falling back to full refresh")
            return self.load(dim_date, dim_customer, dim_product, dim_supplier,
                             fact_sales, quality_issues)

        # Upsert dimensions
        dim_tables = [
            ("dim_date", dim_date, "date_key"),
            ("dim_supplier", dim_supplier, "supplier_id"),
            ("dim_customer", dim_customer, "customer_id"),
            ("dim_product", dim_product, "product_id"),
        ]

        for table_name, df, key_col in dim_tables:
            self._upsert_dimension(table_name, df, key_col)

        # Append only new facts (by order_key)
        new_facts = self._filter_new_facts(fact_sales)

        if len(new_facts) > 0:
            new_facts.to_sql("fact_sales", self.engine, if_exists="append", index=False)

        if quality_issues is not None and len(quality_issues) > 0:
            quality_issues.to_sql("data_quality_issues", self.engine, if_exists="append", index=False)

        # Update metadata
        with self.engine.begin() as conn:
            for table_name, df, _ in dim_tables:
                self._update_metadata(conn, table_name, len(df), "incremental")
            self._update_metadata(conn, "fact_sales", len(new_facts), "incremental")

        # Rebuild aggregates from scratch (fast enough for SQLite)
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM agg_daily_sales"))
        self._build_aggregates()

        return len(new_facts)

    def _upsert_dimension(self, table_name: str, df: pd.DataFrame, key_col: str):
        """Upsert rows into a dimension table based on the business key."""
        if df.empty:
            return

        with self.engine.begin() as conn:
            existing_keys = {
                row[0]
                for row in conn.execute(
                    text(f"SELECT {key_col} FROM {table_name}")
                ).fetchall()
            }

        # Split into updates and inserts
        df_str = df.copy()
        if key_col in df_str.columns:
            new_rows = df_str[~df_str[key_col].isin(existing_keys)]
            update_rows = df_str[df_str[key_col].isin(existing_keys)]
        else:
            new_rows = df_str
            update_rows = pd.DataFrame()

        if len(new_rows) > 0:
            new_rows.to_sql(table_name, self.engine, if_exists="append", index=False)

        if len(update_rows) > 0:
            cols = [c for c in update_rows.columns if c != key_col]
            set_clause = ", ".join(f"{c} = :{c}" for c in cols)
            sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_col} = :{key_col}"
            with self.engine.begin() as conn:
                for _, row in update_rows.iterrows():
                    params = {c: row[c] for c in update_rows.columns}
                    conn.execute(text(sql), params)

    def _filter_new_facts(self, fact_sales: pd.DataFrame) -> pd.DataFrame:
        """Return only fact rows whose order_key does not exist yet."""
        with self.engine.connect() as conn:
            existing = {
                row[0]
                for row in conn.execute(
                    text("SELECT order_key FROM fact_sales")
                ).fetchall()
            }
        return fact_sales[~fact_sales["order_key"].isin(existing)]

    def _build_aggregates(self):
        """Populate aggregate tables from fact data."""
        agg_sql = """
        INSERT INTO agg_daily_sales (date, total_revenue, total_orders, avg_order_value, unique_customers)
        SELECT d.full_date,
               SUM(f.total_amount),
               COUNT(DISTINCT f.order_key),
               ROUND(AVG(f.total_amount), 2),
               COUNT(DISTINCT f.customer_key)
        FROM fact_sales f
        JOIN dim_date d ON f.date_key = d.date_key
        GROUP BY d.full_date
        """
        with self.engine.begin() as conn:
            conn.execute(text(agg_sql))
