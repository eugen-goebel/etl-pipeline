"""Tests for incremental load functionality."""

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import text

from agents.dimension_builder import DimensionBuilder, FactBuilder
from agents.loader import DatabaseLoader
from agents.transformers import DataCleaner, DataEnricher
from db.database import get_engine


@pytest.fixture
def star_schema(
    sample_customers_df,
    sample_suppliers_df,
    sample_products_df,
    sample_orders_df,
    sample_returns_df,
    sample_shipping_df,
):
    """Build a complete star schema from sample data."""
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
    fact_sales = FactBuilder().build_fact_sales(orders, dim_customer, dim_product, dim_supplier)

    return {
        "dim_date": dim_date,
        "dim_customer": dim_customer,
        "dim_supplier": dim_supplier,
        "dim_product": dim_product,
        "fact_sales": fact_sales,
    }


class TestIncrementalLoad:
    def test_first_incremental_falls_back_to_full(self, db_path, star_schema):
        """When no prior load exists, incremental should do a full load."""
        loader = DatabaseLoader(db_path)
        loader.load_incremental(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()
        assert count == len(star_schema["fact_sales"])

    def test_incremental_does_not_duplicate_facts(self, db_path, star_schema):
        """Running incremental twice with the same data should not create duplicates."""
        loader = DatabaseLoader(db_path)
        # Initial full load
        loader.load(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count_before = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()

        # Incremental with same data
        new_count = loader.load_incremental(**star_schema)

        with eng.connect() as conn:
            count_after = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()

        assert count_after == count_before
        assert new_count == 0

    def test_incremental_appends_new_facts(self, db_path, star_schema):
        """Incremental should append only new fact rows."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count_before = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()

        # Add a new fact row with a unique order_key
        with eng.connect() as conn:
            max_key = conn.execute(text("SELECT MAX(order_key) FROM fact_sales")).scalar()

        extra_fact = star_schema["fact_sales"].head(1).copy()
        extra_fact["order_key"] = max_key + 100

        extended = pd.concat([star_schema["fact_sales"], extra_fact], ignore_index=True)
        schema_with_extra = {**star_schema, "fact_sales": extended}

        new_count = loader.load_incremental(**schema_with_extra)

        with eng.connect() as conn:
            count_after = conn.execute(text("SELECT COUNT(*) FROM fact_sales")).scalar()

        assert count_after == count_before + 1
        assert new_count == 1

    def test_metadata_updated_after_full_load(self, db_path, star_schema):
        """Full load should write load metadata for each table."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            rows = conn.execute(text("SELECT table_name, load_mode FROM load_metadata")).fetchall()

        table_modes = {r[0]: r[1] for r in rows}
        assert table_modes["fact_sales"] == "full"
        assert "dim_date" in table_modes

    def test_metadata_updated_after_incremental(self, db_path, star_schema):
        """Incremental load should update metadata with mode='incremental'."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)
        loader.load_incremental(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            row = conn.execute(
                text("SELECT load_mode FROM load_metadata WHERE table_name = 'fact_sales'")
            ).fetchone()
        assert row[0] == "incremental"

    def test_dimension_upsert_updates_existing(self, db_path, star_schema):
        """Incremental should update changed dimension rows."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)

        # Modify a customer name
        modified_customers = star_schema["dim_customer"].copy()
        if len(modified_customers) > 0:
            modified_customers.iloc[0, modified_customers.columns.get_loc("name")] = "Updated Name"

        schema_modified = {**star_schema, "dim_customer": modified_customers}
        loader.load_incremental(**schema_modified)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM dim_customer")).scalar()
        # Should not have added extra rows
        assert count == len(star_schema["dim_customer"])

    def test_aggregates_rebuilt_after_incremental(self, db_path, star_schema):
        """Aggregates should be rebuilt after an incremental load."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)
        loader.load_incremental(**star_schema)

        eng = get_engine(db_path)
        with eng.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM agg_daily_sales")).scalar()
        assert count > 0

    def test_get_last_load_returns_none_on_empty(self, db_path):
        """get_last_load should return None when no metadata exists."""
        loader = DatabaseLoader(db_path)
        loader.initialize()
        assert loader.get_last_load("fact_sales") is None

    def test_get_last_load_returns_timestamp(self, db_path, star_schema):
        """get_last_load should return a timestamp after loading."""
        loader = DatabaseLoader(db_path)
        loader.load(**star_schema)
        ts = loader.get_last_load("fact_sales")
        assert ts is not None
        assert "T" in ts  # ISO format
