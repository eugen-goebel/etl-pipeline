"""Data cleaning and enrichment transformations."""

import pandas as pd
from datetime import date


class DataCleaner:
    """Standardizes, deduplicates, and cleans raw DataFrames."""

    def clean_orders(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df["order_date"] = pd.to_datetime(df["order_date"]).dt.date
        df = df.drop_duplicates(subset=["order_id"])
        df = df[df["status"] != "cancelled"]
        df = df[df["quantity"] > 0]
        df = df[df["unit_price"] > 0]
        return df.reset_index(drop=True)

    def clean_customers(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df["signup_date"] = pd.to_datetime(df["signup_date"]).dt.date
        df = df.drop_duplicates(subset=["customer_id"])
        df["name"] = df["name"].str.strip()
        df["email"] = df["email"].str.lower().str.strip()
        return df.reset_index(drop=True)

    def clean_products(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.drop_duplicates(subset=["product_id"])
        return df.reset_index(drop=True)

    def clean_suppliers(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.drop_duplicates(subset=["supplier_id"])
        return df.reset_index(drop=True)

    def clean_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df["return_date"] = pd.to_datetime(df["return_date"]).dt.date
        df = df.drop_duplicates(subset=["return_id"])
        return df.reset_index(drop=True)

    def clean_shipping(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = [c.strip().lower() for c in df.columns]
        df["shipped_date"] = pd.to_datetime(df["shipped_date"]).dt.date
        df["delivered_date"] = pd.to_datetime(df["delivered_date"]).dt.date
        return df.reset_index(drop=True)


class DataEnricher:
    """Adds derived columns and business calculations."""

    def enrich_orders(self, orders: pd.DataFrame, returns: pd.DataFrame, shipping: pd.DataFrame) -> pd.DataFrame:
        df = orders.copy()

        # Total amount after discount
        df["total_amount"] = df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100)
        df["total_amount"] = df["total_amount"].round(2)

        # Return flag
        returned_orders = set(returns["order_id"].unique()) if len(returns) > 0 else set()
        df["is_returned"] = df["order_id"].isin(returned_orders)

        # Shipping cost
        shipping_costs = shipping.set_index("order_id")["shipping_cost"].to_dict() if len(shipping) > 0 else {}
        df["shipping_cost"] = df["order_id"].map(shipping_costs).fillna(0.0)

        return df

    def enrich_products(self, products: pd.DataFrame) -> pd.DataFrame:
        df = products.copy()
        df["margin_pct"] = ((df["retail_price"] - df["cost_price"]) / df["retail_price"] * 100).round(1)
        return df
