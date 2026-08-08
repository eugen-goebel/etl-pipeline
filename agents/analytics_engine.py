"""SQL analytics engine -- executes pre-built queries against the star schema."""

import os
import re
import time

import pandas as pd
from pandas.errors import DatabaseError
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from db.database import get_engine

# Wall-clock ceiling for user-supplied queries in the SQL Explorer.
QUERY_TIMEOUT_SECONDS = 5.0


class AnalyticsEngine:
    def __init__(self, db_path: str = "output/shopflow.db"):
        self.db_path = db_path
        self.engine = get_engine(db_path)
        self._readonly_engine = None
        self.sql_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sql", "queries"
        )

    def readonly_engine(self):
        """An engine that cannot write, whatever the SQL turns out to say.

        The keyword check in execute_raw is a filter over text, and filters get
        bypassed: a pragma table-valued function and a recursive CTE both slipped
        past earlier versions of it. Opening SQLite in read-only mode moves the
        guarantee from "we hope the filter caught it" to something the database
        enforces, so a statement that does get through still cannot change data.
        """
        if self._readonly_engine is None:
            self._readonly_engine = create_engine(
                f"sqlite:///file:{self.db_path}?mode=ro&uri=true", echo=False
            )
        return self._readonly_engine

    def execute_query(self, query_name: str) -> pd.DataFrame:
        """Load and execute a named SQL query from the sql/queries/ directory."""
        filepath = os.path.join(self.sql_dir, f"{query_name}.sql")
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Query not found: {query_name}")
        with open(filepath) as f:
            sql = f.read()
        return pd.read_sql(sql, self.engine)

    def execute_raw(self, sql: str) -> pd.DataFrame:
        """Execute a read-only SQL query under a time limit.

        Rejects write operations, and aborts anything still running after
        QUERY_TIMEOUT_SECONDS. Without the limit a query that is read-only but
        unbounded (a recursive CTE, say) keeps a shared deployment busy for
        every visitor.
        """
        normalized = sql.strip().upper()
        forbidden = (
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "ALTER",
            "CREATE",
            "ATTACH",
            "DETACH",
            "PRAGMA",
            "VACUUM",
            "REPLACE",
        )
        # Scan every word, not just the first: a write can sit anywhere in the
        # statement, and pragmas are also reachable as pragma_* functions.
        tokens = set(re.findall(r"[A-Za-z_]+", normalized))
        if tokens & set(forbidden) or any(t.startswith("PRAGMA_") for t in tokens):
            raise ValueError("Only SELECT queries are allowed")

        with self.readonly_engine().connect() as conn:
            self._apply_timeout(conn, QUERY_TIMEOUT_SECONDS)
            try:
                return pd.read_sql(sql, conn)
            except (OperationalError, DatabaseError) as exc:
                # pandas wraps the driver error, so match on the message rather
                # than on the exception type.
                if "interrupted" in str(exc).lower():
                    raise ValueError(
                        f"Query cancelled after {QUERY_TIMEOUT_SECONDS} seconds."
                    ) from exc
                raise

    @staticmethod
    def _apply_timeout(conn, seconds: float) -> None:
        """Abort the query once `seconds` have passed, on SQLite.

        SQLite calls the progress handler every N virtual-machine steps; a
        non-zero return aborts the statement. Other backends are left alone.
        """
        raw = getattr(conn.connection, "dbapi_connection", conn.connection)
        handler = getattr(raw, "set_progress_handler", None)
        if handler is None:
            return
        deadline = time.monotonic() + seconds
        handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)

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
        return sorted(
            [f.replace(".sql", "") for f in os.listdir(self.sql_dir) if f.endswith(".sql")]
        )
