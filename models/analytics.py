"""Pydantic models for analytics query results."""

from pydantic import BaseModel


class KPISnapshot(BaseModel):
    total_revenue: float
    total_orders: int
    avg_order_value: float
    unique_customers: int
    return_rate: float
    yoy_growth: float | None = None


class RevenueTrend(BaseModel):
    year: int
    month: int
    month_name: str
    revenue: float
    orders: int
    cumulative_revenue: float
    mom_growth_pct: float | None = None


class CohortEntry(BaseModel):
    cohort_month: str
    months_since_first: int
    active_customers: int


class RFMSegment(BaseModel):
    customer_id: str
    recency_score: int
    frequency_score: int
    monetary_score: int
    segment: str
