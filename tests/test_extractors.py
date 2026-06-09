"""Tests for data extraction agents."""

import pytest

from agents.extractors import APIExtractor, CSVExtractor, JSONExtractor, extract_all


class TestCSVExtractor:
    def test_extract_reads_csv(self, sample_data_dir):
        ext = CSVExtractor()
        df = ext.extract(f"{sample_data_dir}/raw/orders.csv")
        assert len(df) == 5
        assert "order_id" in df.columns

    def test_extract_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            CSVExtractor().extract("/nonexistent/file.csv")


class TestJSONExtractor:
    def test_extract_reads_json(self, sample_data_dir):
        ext = JSONExtractor()
        df = ext.extract(f"{sample_data_dir}/raw/products.json")
        assert len(df) == 3
        assert "product_id" in df.columns

    def test_extract_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            JSONExtractor().extract("/nonexistent/file.json")


class TestAPIExtractor:
    def test_extract_reads_shipping(self, sample_data_dir):
        ext = APIExtractor()
        df = ext.extract(f"{sample_data_dir}/raw/shipping_events.json")
        assert len(df) == 4
        assert "carrier" in df.columns


class TestExtractAll:
    def test_returns_all_sources(self, sample_data_dir):
        sources = extract_all(sample_data_dir)
        assert set(sources.keys()) == {
            "orders",
            "customers",
            "returns",
            "products",
            "suppliers",
            "shipping",
        }

    def test_row_counts(self, sample_data_dir):
        sources = extract_all(sample_data_dir)
        assert sources["orders"].row_count == 5
        assert sources["customers"].row_count == 3
        assert sources["products"].row_count == 3
        assert sources["suppliers"].row_count == 2
        assert sources["returns"].row_count == 1
        assert sources["shipping"].row_count == 4

    def test_columns_present(self, sample_data_dir):
        sources = extract_all(sample_data_dir)
        assert "order_id" in sources["orders"].columns
        assert "customer_id" in sources["customers"].columns
