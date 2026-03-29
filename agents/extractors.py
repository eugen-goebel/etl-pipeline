"""Data extractors for CSV, JSON, and mock API sources."""

import os
import json
import pandas as pd


class CSVExtractor:
    """Extracts data from CSV files into DataFrames."""

    def extract(self, filepath: str) -> pd.DataFrame:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Source file not found: {filepath}")
        df = pd.read_csv(filepath, parse_dates=True)
        return df


class JSONExtractor:
    """Extracts data from JSON files into DataFrames."""

    def extract(self, filepath: str) -> pd.DataFrame:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Source file not found: {filepath}")
        with open(filepath) as f:
            data = json.load(f)
        return pd.DataFrame(data)


class APIExtractor:
    """Extracts data from local JSON mock API (shipping events)."""

    def extract(self, filepath: str) -> pd.DataFrame:
        """Load shipping events from JSON file (simulates API response)."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"API source not found: {filepath}")
        with open(filepath) as f:
            data = json.load(f)
        return pd.DataFrame(data)


class ExtractionResult:
    """Container for extracted data with metadata."""

    def __init__(self, name: str, df: pd.DataFrame, source_path: str):
        self.name = name
        self.df = df
        self.source_path = source_path
        self.row_count = len(df)
        self.columns = list(df.columns)


def extract_all(data_dir: str) -> dict[str, ExtractionResult]:
    """Extract all sources from the data directory."""
    csv_ext = CSVExtractor()
    json_ext = JSONExtractor()
    api_ext = APIExtractor()

    sources = {}

    raw_dir = os.path.join(data_dir, "raw")

    # CSV sources
    for name, filename in [("orders", "orders.csv"), ("customers", "customers.csv"), ("returns", "returns.csv")]:
        path = os.path.join(raw_dir, filename)
        df = csv_ext.extract(path)
        sources[name] = ExtractionResult(name, df, path)

    # JSON sources
    for name, filename in [("products", "products.json"), ("suppliers", "suppliers.json")]:
        path = os.path.join(raw_dir, filename)
        df = json_ext.extract(path)
        sources[name] = ExtractionResult(name, df, path)

    # Mock API
    path = os.path.join(raw_dir, "shipping_events.json")
    df = api_ext.extract(path)
    sources["shipping"] = ExtractionResult("shipping", df, path)

    return sources
