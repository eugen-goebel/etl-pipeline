"""Tests for data cleaning and enrichment transformations."""

from datetime import date

import pandas as pd
import pytest

from agents.transformers import DataCleaner, DataEnricher


@pytest.fixture
def cleaner():
    return DataCleaner()


@pytest.fixture
def enricher():
    return DataEnricher()


class TestDataCleaner:
    def test_clean_orders_removes_cancelled(self, cleaner, sample_orders_df):
        result = cleaner.clean_orders(sample_orders_df)
        assert "cancelled" not in result["status"].values

    def test_clean_orders_deduplicates(self, cleaner, sample_orders_df):
        duped = pd.concat([sample_orders_df, sample_orders_df.iloc[:1]])
        result = cleaner.clean_orders(duped)
        assert result["order_id"].is_unique

    def test_clean_orders_removes_zero_quantity(self, cleaner):
        df = pd.DataFrame(
            [
                {
                    "order_id": "O1",
                    "customer_id": "C1",
                    "product_id": "P1",
                    "quantity": 0,
                    "unit_price": 10,
                    "discount_pct": 0,
                    "order_date": "2024-01-01",
                    "status": "completed",
                },
            ]
        )
        result = cleaner.clean_orders(df)
        assert len(result) == 0

    def test_clean_customers_lowercase_email(self, cleaner, sample_customers_df):
        sample_customers_df.loc[0, "email"] = "MAX@TEST.DE"
        result = cleaner.clean_customers(sample_customers_df)
        assert result.loc[0, "email"] == "max@test.de"

    def test_clean_customers_strips_name(self, cleaner, sample_customers_df):
        sample_customers_df.loc[0, "name"] = "  Max Mueller  "
        result = cleaner.clean_customers(sample_customers_df)
        assert result.loc[0, "name"] == "Max Mueller"

    def test_clean_products_deduplicates(self, cleaner, sample_products_df):
        duped = pd.concat([sample_products_df, sample_products_df.iloc[:1]])
        result = cleaner.clean_products(duped)
        assert result["product_id"].is_unique

    def test_clean_shipping_converts_dates(self, cleaner, sample_shipping_df):
        # Convert to strings to test conversion
        sample_shipping_df["shipped_date"] = sample_shipping_df["shipped_date"].astype(str)
        sample_shipping_df["delivered_date"] = sample_shipping_df["delivered_date"].astype(str)
        result = cleaner.clean_shipping(sample_shipping_df)
        assert result["shipped_date"].iloc[0] == date(2024, 3, 16)

    def test_column_standardization(self, cleaner):
        df = pd.DataFrame(
            [
                {
                    "Order_ID": "O1",
                    "Customer_ID": "C1",
                    "Product_ID": "P1",
                    "Quantity": 1,
                    "Unit_Price": 10,
                    "Discount_Pct": 0,
                    "Order_Date": "2024-01-01",
                    "Status": "completed",
                }
            ]
        )
        result = cleaner.clean_orders(df)
        assert all(c == c.lower() for c in result.columns)


class TestDataEnricher:
    def test_enrich_orders_total_amount(
        self, enricher, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        cleaner = DataCleaner()
        orders = cleaner.clean_orders(sample_orders_df)
        result = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)
        # ORD-00001: qty=1, price=799, disc=0 -> 799.0
        row = result[result["order_id"] == "ORD-00001"].iloc[0]
        assert row["total_amount"] == 799.0

    def test_enrich_orders_discount(
        self, enricher, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        cleaner = DataCleaner()
        orders = cleaner.clean_orders(sample_orders_df)
        result = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)
        # ORD-00002: qty=3, price=24.99, disc=10% -> 3 * 24.99 * 0.9 = 67.47
        row = result[result["order_id"] == "ORD-00002"].iloc[0]
        assert abs(row["total_amount"] - 67.47) < 0.01

    def test_enrich_orders_return_flag(
        self, enricher, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        cleaner = DataCleaner()
        orders = cleaner.clean_orders(sample_orders_df)
        result = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)
        returned = result[result["order_id"] == "ORD-00002"].iloc[0]
        not_returned = result[result["order_id"] == "ORD-00001"].iloc[0]
        assert returned["is_returned"]
        assert not not_returned["is_returned"]

    def test_enrich_orders_shipping_cost(
        self, enricher, sample_orders_df, sample_returns_df, sample_shipping_df
    ):
        cleaner = DataCleaner()
        orders = cleaner.clean_orders(sample_orders_df)
        result = enricher.enrich_orders(orders, sample_returns_df, sample_shipping_df)
        row = result[result["order_id"] == "ORD-00001"].iloc[0]
        assert row["shipping_cost"] == 6.99

    def test_enrich_products_margin(self, enricher, sample_products_df):
        result = enricher.enrich_products(sample_products_df)
        # P001: (800-400)/800 * 100 = 50.0
        row = result[result["product_id"] == "P001"].iloc[0]
        assert row["margin_pct"] == 50.0
