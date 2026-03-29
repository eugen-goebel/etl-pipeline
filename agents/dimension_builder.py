"""Builds star schema dimensions and fact table from cleaned data."""

import pandas as pd
from datetime import date, timedelta


class DimensionBuilder:

    def build_dim_date(self, start_date: date = date(2024, 1, 1), end_date: date = date(2025, 12, 31)) -> pd.DataFrame:
        """Generate a complete date dimension table."""
        dates = []
        current = start_date
        while current <= end_date:
            fiscal_q = f"FQ{((current.month - 1) // 3) + 1}/{current.year}"
            dates.append({
                "date_key": int(current.strftime("%Y%m%d")),
                "full_date": current,
                "year": current.year,
                "quarter": (current.month - 1) // 3 + 1,
                "month": current.month,
                "month_name": current.strftime("%B"),
                "week": current.isocalendar()[1],
                "day_of_week": current.isoweekday(),
                "day_name": current.strftime("%A"),
                "is_weekend": current.isoweekday() >= 6,
                "fiscal_quarter": fiscal_q,
            })
            current += timedelta(days=1)
        return pd.DataFrame(dates)

    def build_dim_customer(self, customers: pd.DataFrame) -> pd.DataFrame:
        """Build customer dimension with surrogate keys."""
        df = customers.copy()
        df = df.reset_index(drop=True)
        df["customer_key"] = df.index + 1
        return df[["customer_key", "customer_id", "name", "email", "region", "city", "segment", "signup_date"]]

    def build_dim_supplier(self, suppliers: pd.DataFrame) -> pd.DataFrame:
        """Build supplier dimension with surrogate keys."""
        df = suppliers.copy()
        df = df.reset_index(drop=True)
        df["supplier_key"] = df.index + 1
        return df[["supplier_key", "supplier_id", "name", "country", "lead_time_days", "reliability_rating"]]

    def build_dim_product(self, products: pd.DataFrame, dim_supplier: pd.DataFrame) -> pd.DataFrame:
        """Build product dimension with surrogate keys and supplier FK."""
        df = products.copy()
        df = df.reset_index(drop=True)
        df["product_key"] = df.index + 1

        supplier_map = dim_supplier.set_index("supplier_id")["supplier_key"].to_dict()
        df["supplier_key"] = df["supplier_id"].map(supplier_map).fillna(0).astype(int)

        return df[["product_key", "product_id", "name", "category", "subcategory", "brand",
                    "supplier_key", "cost_price", "retail_price", "margin_pct"]]


class FactBuilder:

    def build_fact_sales(self, orders: pd.DataFrame, dim_customer: pd.DataFrame,
                         dim_product: pd.DataFrame, dim_supplier: pd.DataFrame) -> pd.DataFrame:
        """Build the fact_sales table with all surrogate keys."""
        df = orders.copy()

        # Map surrogate keys
        customer_map = dim_customer.set_index("customer_id")["customer_key"].to_dict()
        product_map = dim_product.set_index("product_id")["product_key"].to_dict()

        # product -> supplier mapping
        product_supplier = dim_product.set_index("product_key")["supplier_key"].to_dict()

        df["customer_key"] = df["customer_id"].map(customer_map).fillna(0).astype(int)
        df["product_key"] = df["product_id"].map(product_map).fillna(0).astype(int)
        df["supplier_key"] = df["product_key"].map(product_supplier).fillna(0).astype(int)
        df["date_key"] = pd.to_datetime(df["order_date"]).dt.strftime("%Y%m%d").astype(int)

        # Compute profit margin
        product_cost = dim_product.set_index("product_key")["cost_price"].to_dict()
        df["cost"] = df["product_key"].map(product_cost).fillna(0) * df["quantity"]
        df["profit_margin"] = ((df["total_amount"] - df["cost"] - df["shipping_cost"]) / df["total_amount"] * 100).round(1)
        df["profit_margin"] = df["profit_margin"].fillna(0)

        df = df.reset_index(drop=True)
        df["order_key"] = df.index + 1

        return df[["order_key", "date_key", "customer_key", "product_key", "supplier_key",
                    "quantity", "unit_price", "discount_pct", "total_amount", "shipping_cost",
                    "profit_margin", "is_returned"]]
