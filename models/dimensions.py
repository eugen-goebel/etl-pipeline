"""Pydantic models for star schema dimension and fact records."""

from datetime import date

from pydantic import BaseModel


class DimDate(BaseModel):
    date_key: int
    full_date: date
    year: int
    quarter: int
    month: int
    month_name: str
    week: int
    day_of_week: int
    day_name: str
    is_weekend: bool
    fiscal_quarter: str


class DimCustomer(BaseModel):
    customer_key: int
    customer_id: str
    name: str
    email: str
    region: str
    city: str
    segment: str
    signup_date: date


class DimProduct(BaseModel):
    product_key: int
    product_id: str
    name: str
    category: str
    subcategory: str
    brand: str
    supplier_key: int
    cost_price: float
    retail_price: float
    margin_pct: float


class DimSupplier(BaseModel):
    supplier_key: int
    supplier_id: str
    name: str
    country: str
    lead_time_days: int
    reliability_rating: float


class FactSales(BaseModel):
    order_key: int
    date_key: int
    customer_key: int
    product_key: int
    supplier_key: int
    quantity: int
    unit_price: float
    discount_pct: float
    total_amount: float
    shipping_cost: float
    profit_margin: float
    is_returned: bool
