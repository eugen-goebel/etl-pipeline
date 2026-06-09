"""Tests for dimension and fact table builders."""

from datetime import date

import pytest

from agents.dimension_builder import DimensionBuilder, FactBuilder
from agents.transformers import DataCleaner, DataEnricher


@pytest.fixture
def dim_builder():
    return DimensionBuilder()


@pytest.fixture
def built_dimensions(dim_builder, sample_customers_df, sample_suppliers_df, sample_products_df):
    dim_customer = dim_builder.build_dim_customer(sample_customers_df)
    dim_supplier = dim_builder.build_dim_supplier(sample_suppliers_df)
    products_enriched = DataEnricher().enrich_products(sample_products_df)
    dim_product = dim_builder.build_dim_product(products_enriched, dim_supplier)
    return dim_customer, dim_supplier, dim_product


class TestDimensionBuilder:
    def test_dim_date_covers_range(self, dim_builder):
        df = dim_builder.build_dim_date(date(2024, 1, 1), date(2024, 1, 31))
        assert len(df) == 31

    def test_dim_date_columns(self, dim_builder):
        df = dim_builder.build_dim_date(date(2024, 1, 1), date(2024, 1, 7))
        expected = {
            "date_key",
            "full_date",
            "year",
            "quarter",
            "month",
            "month_name",
            "week",
            "day_of_week",
            "day_name",
            "is_weekend",
            "fiscal_quarter",
        }
        assert expected.issubset(set(df.columns))

    def test_dim_date_weekend_flag(self, dim_builder):
        # 2024-01-06 is Saturday, 2024-01-07 is Sunday
        df = dim_builder.build_dim_date(date(2024, 1, 6), date(2024, 1, 7))
        assert df["is_weekend"].all()

    def test_dim_customer_surrogate_keys(self, dim_builder, sample_customers_df):
        df = dim_builder.build_dim_customer(sample_customers_df)
        assert "customer_key" in df.columns
        assert df["customer_key"].is_unique
        assert len(df) == 3

    def test_dim_customer_preserves_all(self, dim_builder, sample_customers_df):
        df = dim_builder.build_dim_customer(sample_customers_df)
        assert set(df["customer_id"]) == {"C0001", "C0002", "C0003"}

    def test_dim_supplier_surrogate_keys(self, dim_builder, sample_suppliers_df):
        df = dim_builder.build_dim_supplier(sample_suppliers_df)
        assert "supplier_key" in df.columns
        assert df["supplier_key"].is_unique

    def test_dim_product_maps_supplier(self, built_dimensions):
        _, dim_supplier, dim_product = built_dimensions
        # All products should have a valid supplier_key
        valid_keys = set(dim_supplier["supplier_key"])
        assert all(k in valid_keys for k in dim_product["supplier_key"])


class TestFactBuilder:
    def test_fact_sales_columns(
        self, built_dimensions, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        dim_customer, dim_supplier, dim_product = built_dimensions
        cleaner = DataCleaner()
        enricher = DataEnricher()
        orders = cleaner.clean_orders(sample_orders_df)
        orders = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)

        fb = FactBuilder()
        fact = fb.build_fact_sales(orders, dim_customer, dim_product, dim_supplier)
        required = {
            "order_key",
            "date_key",
            "customer_key",
            "product_key",
            "supplier_key",
            "quantity",
            "unit_price",
            "discount_pct",
            "total_amount",
            "shipping_cost",
            "profit_margin",
            "is_returned",
        }
        assert required.issubset(set(fact.columns))

    def test_fact_sales_date_key_format(
        self, built_dimensions, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        dim_customer, dim_supplier, dim_product = built_dimensions
        cleaner = DataCleaner()
        enricher = DataEnricher()
        orders = cleaner.clean_orders(sample_orders_df)
        orders = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)

        fb = FactBuilder()
        fact = fb.build_fact_sales(orders, dim_customer, dim_product, dim_supplier)
        # date_key should be YYYYMMDD format
        for dk in fact["date_key"]:
            assert 20240101 <= dk <= 20251231

    def test_fact_sales_profit_margin(
        self, built_dimensions, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        dim_customer, dim_supplier, dim_product = built_dimensions
        cleaner = DataCleaner()
        enricher = DataEnricher()
        orders = cleaner.clean_orders(sample_orders_df)
        orders = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)

        fb = FactBuilder()
        fact = fb.build_fact_sales(orders, dim_customer, dim_product, dim_supplier)
        assert "profit_margin" in fact.columns
        # Profit margin should be a numeric column
        assert fact["profit_margin"].dtype in ("float64", "float32")
