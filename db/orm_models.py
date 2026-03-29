"""SQLAlchemy ORM models for the star schema."""

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Index
from db.database import Base


class DimDateTable(Base):
    __tablename__ = "dim_date"

    date_key = Column(Integer, primary_key=True)
    full_date = Column(Date, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    month_name = Column(String, nullable=False)
    week = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)
    day_name = Column(String, nullable=False)
    is_weekend = Column(Boolean, nullable=False)
    fiscal_quarter = Column(String, nullable=False)


class DimCustomerTable(Base):
    __tablename__ = "dim_customer"

    customer_key = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    region = Column(String, nullable=False)
    city = Column(String, nullable=False)
    segment = Column(String, nullable=False)
    signup_date = Column(Date, nullable=False)


class DimSupplierTable(Base):
    __tablename__ = "dim_supplier"

    supplier_key = Column(Integer, primary_key=True, autoincrement=True)
    supplier_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    reliability_rating = Column(Float, nullable=False)


class DimProductTable(Base):
    __tablename__ = "dim_product"

    product_key = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    supplier_key = Column(Integer, ForeignKey("dim_supplier.supplier_key"), nullable=False)
    cost_price = Column(Float, nullable=False)
    retail_price = Column(Float, nullable=False)
    margin_pct = Column(Float, nullable=False)


class FactSalesTable(Base):
    __tablename__ = "fact_sales"

    order_key = Column(Integer, primary_key=True, autoincrement=True)
    date_key = Column(Integer, ForeignKey("dim_date.date_key"), nullable=False)
    customer_key = Column(Integer, ForeignKey("dim_customer.customer_key"), nullable=False)
    product_key = Column(Integer, ForeignKey("dim_product.product_key"), nullable=False)
    supplier_key = Column(Integer, ForeignKey("dim_supplier.supplier_key"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    discount_pct = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    shipping_cost = Column(Float, nullable=False)
    profit_margin = Column(Float, nullable=False)
    is_returned = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        Index("ix_fact_sales_date_key", "date_key"),
        Index("ix_fact_sales_customer_key", "customer_key"),
        Index("ix_fact_sales_product_key", "product_key"),
    )


class AggDailySalesTable(Base):
    __tablename__ = "agg_daily_sales"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    total_revenue = Column(Float, nullable=False)
    total_orders = Column(Integer, nullable=False)
    avg_order_value = Column(Float, nullable=False)
    unique_customers = Column(Integer, nullable=False)


class DataQualityIssueTable(Base):
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String, nullable=False)
    row_index = Column(Integer, nullable=False)
    field = Column(String, nullable=False)
    value = Column(String, nullable=False)
    rule = Column(String, nullable=False)
    message = Column(String, nullable=False)
