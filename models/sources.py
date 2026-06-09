"""Pydantic models for raw source data validation."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class RawOrder(BaseModel):
    order_id: str
    customer_id: str
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    discount_pct: float = Field(ge=0, le=100)
    order_date: date
    status: Literal["completed", "cancelled", "pending"]


class RawCustomer(BaseModel):
    customer_id: str
    name: str
    email: str
    region: str
    city: str
    segment: Literal["B2B", "B2C"]
    signup_date: date


class RawProduct(BaseModel):
    product_id: str
    name: str
    category: str
    subcategory: str
    brand: str
    supplier_id: str
    cost_price: float = Field(gt=0)
    retail_price: float = Field(gt=0)


class RawSupplier(BaseModel):
    supplier_id: str
    name: str
    country: str
    lead_time_days: int = Field(gt=0)
    reliability_rating: float = Field(ge=1, le=5)


class RawReturn(BaseModel):
    return_id: str
    order_id: str
    return_date: date
    reason: str


class RawShippingEvent(BaseModel):
    order_id: str
    carrier: str
    shipped_date: date
    delivered_date: date
    shipping_cost: float = Field(ge=0)
