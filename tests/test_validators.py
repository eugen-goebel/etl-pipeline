"""Tests for data quality validation."""

import pandas as pd
import pytest

from agents.extractors import ExtractionResult, extract_all
from agents.validators import DataValidator


@pytest.fixture
def validator():
    return DataValidator()


def _make_source(name, df):
    return ExtractionResult(name, df, f"/fake/{name}")


class TestDataValidator:
    def test_valid_data_high_score(self, validator, sample_data_dir):
        sources = extract_all(sample_data_dir)
        report = validator.validate_all(sources)
        assert report.overall_score > 90

    def test_null_values_detected(self, validator):
        df = pd.DataFrame([{"order_id": None, "quantity": 1, "unit_price": 10}])
        sources = {"orders": _make_source("orders", df)}
        report = validator.validate_all(sources)
        null_issues = [i for i in report.sources[0].issues if i.rule == "not_null"]
        assert len(null_issues) >= 1

    def test_negative_quantity_flagged(self, validator):
        df = pd.DataFrame(
            [
                {
                    "order_id": "O1",
                    "customer_id": "C1",
                    "product_id": "P1",
                    "quantity": -5,
                    "unit_price": 10,
                    "discount_pct": 0,
                    "order_date": "2024-01-01",
                    "status": "completed",
                },
            ]
        )
        sources = {"orders": _make_source("orders", df)}
        report = validator.validate_all(sources)
        qty_issues = [i for i in report.sources[0].issues if i.field == "quantity"]
        assert len(qty_issues) >= 1

    def test_negative_price_flagged(self, validator):
        df = pd.DataFrame(
            [
                {
                    "order_id": "O1",
                    "customer_id": "C1",
                    "product_id": "P1",
                    "quantity": 1,
                    "unit_price": -10,
                    "discount_pct": 0,
                    "order_date": "2024-01-01",
                    "status": "completed",
                },
            ]
        )
        sources = {"orders": _make_source("orders", df)}
        report = validator.validate_all(sources)
        price_issues = [i for i in report.sources[0].issues if i.field == "unit_price"]
        assert len(price_issues) >= 1

    def test_discount_out_of_range(self, validator):
        df = pd.DataFrame(
            [
                {
                    "order_id": "O1",
                    "customer_id": "C1",
                    "product_id": "P1",
                    "quantity": 1,
                    "unit_price": 10,
                    "discount_pct": 150,
                    "order_date": "2024-01-01",
                    "status": "completed",
                },
            ]
        )
        sources = {"orders": _make_source("orders", df)}
        report = validator.validate_all(sources)
        disc_issues = [i for i in report.sources[0].issues if i.field == "discount_pct"]
        assert len(disc_issues) >= 1

    def test_duplicate_customer_detected(self, validator):
        df = pd.DataFrame(
            [
                {
                    "customer_id": "C1",
                    "name": "A",
                    "email": "a@b.de",
                    "region": "Nord",
                    "city": "HH",
                    "segment": "B2C",
                    "signup_date": "2024-01-01",
                },
                {
                    "customer_id": "C1",
                    "name": "A",
                    "email": "a@b.de",
                    "region": "Nord",
                    "city": "HH",
                    "segment": "B2C",
                    "signup_date": "2024-01-01",
                },
            ]
        )
        sources = {"customers": _make_source("customers", df)}
        report = validator.validate_all(sources)
        dup_issues = [i for i in report.sources[0].issues if i.rule == "unique"]
        assert len(dup_issues) >= 1

    def test_cost_exceeds_retail(self, validator):
        df = pd.DataFrame(
            [
                {
                    "product_id": "P1",
                    "name": "X",
                    "category": "A",
                    "subcategory": "B",
                    "brand": "C",
                    "supplier_id": "S1",
                    "cost_price": 100,
                    "retail_price": 50,
                },
            ]
        )
        sources = {"products": _make_source("products", df)}
        report = validator.validate_all(sources)
        biz_issues = [i for i in report.sources[0].issues if i.rule == "business_rule"]
        assert len(biz_issues) >= 1

    def test_referential_integrity_missing_customer(self, validator, sample_data_dir):
        sources = extract_all(sample_data_dir)
        # Replace a customer_id in orders with one that does not exist
        sources["orders"].df.loc[0, "customer_id"] = "C9999"
        report = validator.validate_all(sources)
        ref_issues = [
            i for s in report.sources for i in s.issues if i.rule == "referential_integrity"
        ]
        assert len(ref_issues) >= 1

    def test_report_structure(self, validator, sample_data_dir):
        sources = extract_all(sample_data_dir)
        report = validator.validate_all(sources)
        assert hasattr(report, "overall_score")
        assert hasattr(report, "total_quarantined")
        assert hasattr(report, "generated_at")
        assert len(report.sources) > 0
