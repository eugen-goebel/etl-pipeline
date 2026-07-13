"""Tests for Pydantic data models."""

from datetime import date

import pytest
from pydantic import ValidationError

from models.dimensions import DimDate, FactSales
from models.quality import DataQualityReport, SourceQuality, ValidationIssue
from models.sources import RawCustomer, RawOrder, RawProduct, RawSupplier


class TestSourceModels:
    def test_raw_order_valid(self):
        order = RawOrder(
            order_id="O1",
            customer_id="C1",
            product_id="P1",
            quantity=2,
            unit_price=10.0,
            discount_pct=5,
            order_date=date(2024, 1, 1),
            status="completed",
        )
        assert order.quantity == 2

    def test_raw_order_negative_quantity(self):
        with pytest.raises(ValidationError):
            RawOrder(
                order_id="O1",
                customer_id="C1",
                product_id="P1",
                quantity=-1,
                unit_price=10.0,
                discount_pct=5,
                order_date=date(2024, 1, 1),
                status="completed",
            )

    def test_raw_order_negative_price(self):
        with pytest.raises(ValidationError):
            RawOrder(
                order_id="O1",
                customer_id="C1",
                product_id="P1",
                quantity=1,
                unit_price=-10.0,
                discount_pct=5,
                order_date=date(2024, 1, 1),
                status="completed",
            )

    def test_raw_customer_valid(self):
        customer = RawCustomer(
            customer_id="C1",
            name="Max",
            email="max@test.de",
            region="Nord",
            city="Hamburg",
            segment="B2C",
            signup_date=date(2024, 1, 1),
        )
        assert customer.segment == "B2C"

    def test_raw_product_valid(self):
        product = RawProduct(
            product_id="P1",
            name="Laptop",
            category="Electronics",
            subcategory="Laptops",
            brand="TechPro",
            supplier_id="S1",
            cost_price=400.0,
            retail_price=800.0,
        )
        assert product.retail_price == 800.0

    def test_raw_supplier_valid(self):
        supplier = RawSupplier(
            supplier_id="S1",
            name="Test GmbH",
            country="DE",
            lead_time_days=5,
            reliability_rating=4.5,
        )
        assert supplier.country == "DE"


class TestDimensionModels:
    def test_dim_date(self):
        d = DimDate(
            date_key=20240101,
            full_date=date(2024, 1, 1),
            year=2024,
            quarter=1,
            month=1,
            month_name="January",
            week=1,
            day_of_week=1,
            day_name="Monday",
            is_weekend=False,
            fiscal_quarter="FQ1/2024",
        )
        assert d.year == 2024

    def test_fact_sales(self):
        f = FactSales(
            order_key=1,
            date_key=20240101,
            customer_key=1,
            product_key=1,
            supplier_key=1,
            quantity=2,
            unit_price=100.0,
            discount_pct=10,
            total_amount=180.0,
            shipping_cost=5.0,
            profit_margin=25.0,
            is_returned=False,
        )
        assert f.total_amount == 180.0


class TestQualityModels:
    def test_validation_issue(self):
        issue = ValidationIssue(
            source="orders",
            row_index=0,
            field="quantity",
            value="-1",
            rule="positive_value",
            message="Must be positive",
        )
        assert issue.source == "orders"

    def test_source_quality(self):
        sq = SourceQuality(
            source_name="orders",
            total_rows=100,
            valid_rows=95,
            invalid_rows=5,
            quality_score=95.0,
            issues=[],
        )
        assert sq.quality_score == 95.0

    def test_quality_report(self):
        report = DataQualityReport(
            sources=[],
            overall_score=100.0,
            total_quarantined=0,
            generated_at="2024-01-01T00:00:00",
        )
        assert report.overall_score == 100.0
