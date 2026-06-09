"""Tests for the database loader."""

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import text

from agents.dimension_builder import DimensionBuilder, FactBuilder
from agents.loader import DatabaseLoader
from agents.transformers import DataCleaner, DataEnricher
from db.database import get_engine


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


class TestDatabaseLoader:
    def test_creates_tables(self, db_path):
        loader = DatabaseLoader(db_path)
        loader.initialize()
        eng = get_engine(db_path)
        with eng.connect() as conn:
            tables = conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            ).fetchall()
        table_names = {t[0] for t in tables}
        assert "dim_date" in table_names
        assert "fact_sales" in table_names

    def test_loads_data(self, loaded_db):
        eng = get_engine(loaded_db)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()
        assert count > 0

    def test_idempotent_reload(
        self,
        loaded_db,
        sample_customers_df,
        sample_suppliers_df,
        sample_products_df,
        sample_orders_df,
        sample_returns_df,
        sample_shipping_df,
    ):
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

        # Load again
        loader = DatabaseLoader(loaded_db)
        loader.load(dim_date, dim_customer, dim_product, dim_supplier, fact)

        eng = get_engine(loaded_db)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()
        # Should have same count, not doubled
        assert count == len(fact)

    def test_aggregates_populated(self, loaded_db):
        eng = get_engine(loaded_db)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM agg_daily_sales")).scalar()
        assert count > 0

    def test_quality_issues_loaded(
        self,
        db_path,
        sample_customers_df,
        sample_suppliers_df,
        sample_products_df,
        sample_orders_df,
        sample_returns_df,
        sample_shipping_df,
    ):
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

        quality_df = pd.DataFrame(
            [
                {
                    "source": "orders",
                    "row_index": 0,
                    "field": "qty",
                    "value": "-1",
                    "rule": "positive",
                    "message": "bad",
                },
            ]
        )
        loader = DatabaseLoader(db_path)
        loader.load(dim_date, dim_customer, dim_product, dim_supplier, fact, quality_df)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM data_quality_issues")).scalar()
        assert count == 1
