"""Tests for the analytics engine."""

import time

import pytest

from agents import analytics_engine
from agents.analytics_engine import AnalyticsEngine


@pytest.fixture
def analytics(loaded_db):
    return AnalyticsEngine(loaded_db)


@pytest.fixture
def loaded_db(
    db_path,
    sample_customers_df,
    sample_suppliers_df,
    sample_products_df,
    sample_orders_df,
    sample_returns_df,
    sample_shipping_df,
):
    """Build and load a complete star schema into a temp DB."""
    from datetime import date

    from agents.dimension_builder import DimensionBuilder, FactBuilder
    from agents.loader import DatabaseLoader
    from agents.transformers import DataCleaner, DataEnricher

    dim_builder = DimensionBuilder()
    cleaner = DataCleaner()
    enricher = DataEnricher()

    dim_date = dim_builder.build_dim_date(date(2024, 1, 1), date(2024, 12, 31))
    dim_customer = dim_builder.build_dim_customer(sample_customers_df)
    dim_supplier = dim_builder.build_dim_supplier(sample_suppliers_df)
    products = enricher.enrich_products(sample_products_df)
    dim_product = dim_builder.build_dim_product(products, dim_supplier)
    orders = cleaner.clean_orders(sample_orders_df)
    orders = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)
    fact = FactBuilder().build_fact_sales(orders, dim_customer, dim_product, dim_supplier)

    loader = DatabaseLoader(db_path)
    loader.load(dim_date, dim_customer, dim_product, dim_supplier, fact)
    return db_path


class TestAnalyticsEngine:
    def test_get_kpis_keys(self, analytics):
        kpis = analytics.get_kpis()
        assert "total_revenue" in kpis
        assert "total_orders" in kpis
        assert "avg_order_value" in kpis
        assert "unique_customers" in kpis
        assert "return_rate" in kpis

    def test_kpis_positive_revenue(self, analytics):
        kpis = analytics.get_kpis()
        assert kpis["total_revenue"] > 0

    def test_execute_raw(self, analytics):
        df = analytics.execute_raw("SELECT COUNT(*) AS cnt FROM fact_sales")
        assert df.iloc[0]["cnt"] > 0

    def test_get_available_queries(self, analytics):
        queries = analytics.get_available_queries()
        assert "revenue_trends" in queries
        assert "rfm_segmentation" in queries
        assert len(queries) == 15

    def test_execute_query_revenue_trends(self, analytics):
        df = analytics.execute_query("revenue_trends")
        assert len(df) > 0
        assert "revenue" in df.columns

    def test_execute_query_not_found(self, analytics):
        with pytest.raises(FileNotFoundError):
            analytics.execute_query("nonexistent_query")


class TestExecuteRawGuards:
    """The SQL Explorer runs visitor-supplied SQL, so execute_raw is a boundary.

    These build their own throwaway database rather than the loaded star
    schema: the guards are about the SQL text and the time limit, not the data.
    """

    @pytest.fixture
    def engine(self, tmp_path):
        return AnalyticsEngine(str(tmp_path / "guard.db"))

    def test_plain_select_still_works(self, engine):
        assert engine.execute_raw("SELECT 1 AS x").iloc[0]["x"] == 1

    def test_blocks_pragma_functions(self, engine):
        # SQLite reaches pragmas through table-valued functions as well, and
        # pragma_database_list() reports the database file path. The name is a
        # single token, so a check for the bare PRAGMA keyword never sees it.
        with pytest.raises(ValueError, match="Only SELECT"):
            engine.execute_raw("SELECT * FROM pragma_database_list()")

    def test_blocks_a_write_that_is_not_the_first_word(self, engine):
        with pytest.raises(ValueError, match="Only SELECT"):
            engine.execute_raw("SELECT 1 WHERE 1=0; DROP TABLE dim_product")

    def test_aborts_a_runaway_query(self, engine, monkeypatch):
        # A recursive CTE is read-only, so no keyword filter can reject it on
        # content. The time limit is what stops one visitor from tying up a
        # shared deployment for everyone else.
        monkeypatch.setattr(analytics_engine, "QUERY_TIMEOUT_SECONDS", 1.0)
        started = time.monotonic()
        with pytest.raises(ValueError, match="cancelled"):
            engine.execute_raw(
                "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) "
                "SELECT count(*) FROM c"
            )
        assert time.monotonic() - started < 15  # aborted, not run to completion
