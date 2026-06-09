"""Shared test fixtures for the ETL pipeline test suite."""

import csv
import json
from datetime import date

import pandas as pd
import pytest


@pytest.fixture
def sample_customers_df():
    return pd.DataFrame(
        [
            {
                "customer_id": "C0001",
                "name": "Max Mueller",
                "email": "max@test.de",
                "region": "Nord",
                "city": "Hamburg",
                "segment": "B2C",
                "signup_date": date(2024, 1, 15),
            },
            {
                "customer_id": "C0002",
                "name": "Anna Schmidt",
                "email": "anna@test.de",
                "region": "Sued",
                "city": "Muenchen",
                "segment": "B2B",
                "signup_date": date(2024, 3, 20),
            },
            {
                "customer_id": "C0003",
                "name": "Peter Weber",
                "email": "peter@test.de",
                "region": "West",
                "city": "Koeln",
                "segment": "B2C",
                "signup_date": date(2024, 6, 10),
            },
        ]
    )


@pytest.fixture
def sample_suppliers_df():
    return pd.DataFrame(
        [
            {
                "supplier_id": "SUP-01",
                "name": "TechLieferant GmbH",
                "country": "DE",
                "lead_time_days": 5,
                "reliability_rating": 4.5,
            },
            {
                "supplier_id": "SUP-02",
                "name": "AsiaImport AG",
                "country": "CN",
                "lead_time_days": 20,
                "reliability_rating": 3.2,
            },
        ]
    )


@pytest.fixture
def sample_products_df():
    return pd.DataFrame(
        [
            {
                "product_id": "P001",
                "name": "Laptop Pro",
                "category": "Elektronik",
                "subcategory": "Laptops",
                "brand": "TechPro",
                "supplier_id": "SUP-01",
                "cost_price": 400.0,
                "retail_price": 800.0,
            },
            {
                "product_id": "P002",
                "name": "T-Shirt Basic",
                "category": "Kleidung",
                "subcategory": "T-Shirts",
                "brand": "StyleWear",
                "supplier_id": "SUP-01",
                "cost_price": 10.0,
                "retail_price": 25.0,
            },
            {
                "product_id": "P003",
                "name": "Yoga Matte",
                "category": "Sport",
                "subcategory": "Fitness",
                "brand": "FitLife",
                "supplier_id": "SUP-02",
                "cost_price": 15.0,
                "retail_price": 35.0,
            },
        ]
    )


@pytest.fixture
def sample_orders_df():
    return pd.DataFrame(
        [
            {
                "order_id": "ORD-00001",
                "customer_id": "C0001",
                "product_id": "P001",
                "quantity": 1,
                "unit_price": 799.0,
                "discount_pct": 0,
                "order_date": date(2024, 3, 15),
                "status": "completed",
            },
            {
                "order_id": "ORD-00002",
                "customer_id": "C0002",
                "product_id": "P002",
                "quantity": 3,
                "unit_price": 24.99,
                "discount_pct": 10,
                "order_date": date(2024, 4, 20),
                "status": "completed",
            },
            {
                "order_id": "ORD-00003",
                "customer_id": "C0001",
                "product_id": "P003",
                "quantity": 2,
                "unit_price": 34.50,
                "discount_pct": 0,
                "order_date": date(2024, 5, 10),
                "status": "completed",
            },
            {
                "order_id": "ORD-00004",
                "customer_id": "C0003",
                "product_id": "P001",
                "quantity": 1,
                "unit_price": 789.0,
                "discount_pct": 15,
                "order_date": date(2024, 6, 1),
                "status": "cancelled",
            },
            {
                "order_id": "ORD-00005",
                "customer_id": "C0003",
                "product_id": "P002",
                "quantity": 5,
                "unit_price": 25.0,
                "discount_pct": 5,
                "order_date": date(2024, 7, 12),
                "status": "completed",
            },
        ]
    )


@pytest.fixture
def sample_returns_df():
    return pd.DataFrame(
        [
            {
                "return_id": "RET-0001",
                "order_id": "ORD-00002",
                "return_date": date(2024, 5, 5),
                "reason": "Falsche Groesse",
            },
        ]
    )


@pytest.fixture
def sample_shipping_df():
    return pd.DataFrame(
        [
            {
                "order_id": "ORD-00001",
                "carrier": "DHL",
                "shipped_date": date(2024, 3, 16),
                "delivered_date": date(2024, 3, 19),
                "shipping_cost": 6.99,
            },
            {
                "order_id": "ORD-00002",
                "carrier": "DPD",
                "shipped_date": date(2024, 4, 21),
                "delivered_date": date(2024, 4, 24),
                "shipping_cost": 4.49,
            },
            {
                "order_id": "ORD-00003",
                "carrier": "Hermes",
                "shipped_date": date(2024, 5, 11),
                "delivered_date": date(2024, 5, 15),
                "shipping_cost": 3.99,
            },
            {
                "order_id": "ORD-00005",
                "carrier": "GLS",
                "shipped_date": date(2024, 7, 13),
                "delivered_date": date(2024, 7, 16),
                "shipping_cost": 5.49,
            },
        ]
    )


@pytest.fixture
def sample_data_dir(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    # customers.csv
    customers = [
        {
            "customer_id": "C0001",
            "name": "Max Mueller",
            "email": "max@test.de",
            "region": "Nord",
            "city": "Hamburg",
            "segment": "B2C",
            "signup_date": "2024-01-15",
        },
        {
            "customer_id": "C0002",
            "name": "Anna Schmidt",
            "email": "anna@test.de",
            "region": "Sued",
            "city": "Muenchen",
            "segment": "B2B",
            "signup_date": "2024-03-20",
        },
        {
            "customer_id": "C0003",
            "name": "Peter Weber",
            "email": "peter@test.de",
            "region": "West",
            "city": "Koeln",
            "segment": "B2C",
            "signup_date": "2024-06-10",
        },
    ]
    with open(raw_dir / "customers.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(customers[0].keys()))
        w.writeheader()
        w.writerows(customers)

    # orders.csv
    orders = [
        {
            "order_id": "ORD-00001",
            "customer_id": "C0001",
            "product_id": "P001",
            "quantity": 1,
            "unit_price": 799.0,
            "discount_pct": 0,
            "order_date": "2024-03-15",
            "status": "completed",
        },
        {
            "order_id": "ORD-00002",
            "customer_id": "C0002",
            "product_id": "P002",
            "quantity": 3,
            "unit_price": 24.99,
            "discount_pct": 10,
            "order_date": "2024-04-20",
            "status": "completed",
        },
        {
            "order_id": "ORD-00003",
            "customer_id": "C0001",
            "product_id": "P003",
            "quantity": 2,
            "unit_price": 34.50,
            "discount_pct": 0,
            "order_date": "2024-05-10",
            "status": "completed",
        },
        {
            "order_id": "ORD-00004",
            "customer_id": "C0003",
            "product_id": "P001",
            "quantity": 1,
            "unit_price": 789.0,
            "discount_pct": 15,
            "order_date": "2024-06-01",
            "status": "cancelled",
        },
        {
            "order_id": "ORD-00005",
            "customer_id": "C0003",
            "product_id": "P002",
            "quantity": 5,
            "unit_price": 25.0,
            "discount_pct": 5,
            "order_date": "2024-07-12",
            "status": "completed",
        },
    ]
    with open(raw_dir / "orders.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(orders[0].keys()))
        w.writeheader()
        w.writerows(orders)

    # returns.csv
    returns = [
        {
            "return_id": "RET-0001",
            "order_id": "ORD-00002",
            "return_date": "2024-05-05",
            "reason": "Falsche Groesse",
        },
    ]
    with open(raw_dir / "returns.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(returns[0].keys()))
        w.writeheader()
        w.writerows(returns)

    # products.json
    products = [
        {
            "product_id": "P001",
            "name": "Laptop Pro",
            "category": "Elektronik",
            "subcategory": "Laptops",
            "brand": "TechPro",
            "supplier_id": "SUP-01",
            "cost_price": 400.0,
            "retail_price": 800.0,
        },
        {
            "product_id": "P002",
            "name": "T-Shirt Basic",
            "category": "Kleidung",
            "subcategory": "T-Shirts",
            "brand": "StyleWear",
            "supplier_id": "SUP-01",
            "cost_price": 10.0,
            "retail_price": 25.0,
        },
        {
            "product_id": "P003",
            "name": "Yoga Matte",
            "category": "Sport",
            "subcategory": "Fitness",
            "brand": "FitLife",
            "supplier_id": "SUP-02",
            "cost_price": 15.0,
            "retail_price": 35.0,
        },
    ]
    with open(raw_dir / "products.json", "w") as f:
        json.dump(products, f)

    # suppliers.json
    suppliers = [
        {
            "supplier_id": "SUP-01",
            "name": "TechLieferant GmbH",
            "country": "DE",
            "lead_time_days": 5,
            "reliability_rating": 4.5,
        },
        {
            "supplier_id": "SUP-02",
            "name": "AsiaImport AG",
            "country": "CN",
            "lead_time_days": 20,
            "reliability_rating": 3.2,
        },
    ]
    with open(raw_dir / "suppliers.json", "w") as f:
        json.dump(suppliers, f)

    # shipping_events.json
    shipping = [
        {
            "order_id": "ORD-00001",
            "carrier": "DHL",
            "shipped_date": "2024-03-16",
            "delivered_date": "2024-03-19",
            "shipping_cost": 6.99,
        },
        {
            "order_id": "ORD-00002",
            "carrier": "DPD",
            "shipped_date": "2024-04-21",
            "delivered_date": "2024-04-24",
            "shipping_cost": 4.49,
        },
        {
            "order_id": "ORD-00003",
            "carrier": "Hermes",
            "shipped_date": "2024-05-11",
            "delivered_date": "2024-05-15",
            "shipping_cost": 3.99,
        },
        {
            "order_id": "ORD-00005",
            "carrier": "GLS",
            "shipped_date": "2024-07-13",
            "delivered_date": "2024-07-16",
            "shipping_cost": 5.49,
        },
    ]
    with open(raw_dir / "shipping_events.json", "w") as f:
        json.dump(shipping, f)

    return str(tmp_path)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")
