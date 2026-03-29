"""Database loader -- idempotent load of star schema into SQLite."""

import os
import pandas as pd
from sqlalchemy import text
from db.database import Base, get_engine
from db.orm_models import (DimDateTable, DimCustomerTable, DimSupplierTable,
                           DimProductTable, FactSalesTable, AggDailySalesTable,
                           DataQualityIssueTable)


class DatabaseLoader:

    def __init__(self, db_path: str = "output/shopflow.db"):
        self.engine = get_engine(db_path)
        self.db_path = db_path

    def initialize(self):
        """Create all tables (idempotent)."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        Base.metadata.create_all(self.engine)

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

        # Build aggregates
        self._build_aggregates()

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
