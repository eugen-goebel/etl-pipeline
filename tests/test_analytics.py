"""Tests for the analytics engine."""

import pytest
from agents.analytics_engine import AnalyticsEngine


@pytest.fixture
def analytics(loaded_db):
    return AnalyticsEngine(loaded_db)


@pytest.fixture
def loaded_db(db_path, sample_customers_df, sample_suppliers_df, sample_products_df,
              sample_orders_df, sample_returns_df, sample_shipping_df):
    """Build and load a complete star schema into a temp DB."""
    from datetime import date
    from agents.loader import DatabaseLoader
    from agents.dimension_builder import DimensionBuilder, FactBuilder
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
