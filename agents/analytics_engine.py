"""SQL analytics engine -- executes pre-built queries against the star schema."""

import os
import pandas as pd
from sqlalchemy import text
from db.database import get_engine


class AnalyticsEngine:

    def __init__(self, db_path: str = "output/shopflow.db"):
        self.engine = get_engine(db_path)
        self.sql_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "queries")

    def execute_query(self, query_name: str) -> pd.DataFrame:
        """Load and execute a named SQL query from the sql/queries/ directory."""
        filepath = os.path.join(self.sql_dir, f"{query_name}.sql")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Query not found: {query_name}")
        with open(filepath) as f:
            sql = f.read()
        return pd.read_sql(sql, self.engine)

    def execute_raw(self, sql: str) -> pd.DataFrame:
        """Execute a read-only SQL query. Rejects write operations."""
        normalized = sql.strip().upper()
        forbidden = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "ATTACH", "DETACH", "PRAGMA")
        if any(normalized.startswith(kw) for kw in forbidden):
            raise ValueError("Only SELECT queries are allowed")
        return pd.read_sql(sql, self.engine)

    def get_kpis(self) -> dict:
        """Calculate executive KPI snapshot."""
        sql = """
        SELECT
            ROUND(SUM(total_amount), 2) AS total_revenue,
            COUNT(DISTINCT order_key) AS total_orders,
            ROUND(AVG(total_amount), 2) AS avg_order_value,
            COUNT(DISTINCT customer_key) AS unique_customers,
            ROUND(SUM(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) / COUNT(*) * 100, 1) AS return_rate
        FROM fact_sales
        """
        result = pd.read_sql(sql, self.engine)
        return result.iloc[0].to_dict()

    def get_available_queries(self) -> list[str]:
        """List all available SQL query names."""
        if not os.path.exists(self.sql_dir):
            return []
        return sorted([f.replace(".sql", "") for f in os.listdir(self.sql_dir) if f.endswith(".sql")])
