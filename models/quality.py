"""Pydantic models for data quality reporting."""

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    source: str
    row_index: int
    field: str
    value: str
    rule: str
    message: str


class SourceQuality(BaseModel):
    source_name: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    quality_score: float = Field(ge=0, le=100)
    issues: list[ValidationIssue]


class DataQualityReport(BaseModel):
    sources: list[SourceQuality]
    overall_score: float
    total_quarantined: int
    generated_at: str
