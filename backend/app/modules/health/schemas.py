from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.database.enums import TimelineEventType


class HealthTrendPoint(BaseModel):
    date: date
    value: float
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    document_id: UUID


class HealthTrendSeries(BaseModel):
    test_name: str
    unit: str | None = None
    points: list[HealthTrendPoint] = Field(default_factory=list)


class HealthTrendsResponse(BaseModel):
    family_member_id: UUID
    series: list[HealthTrendSeries]
    total_measurements: int = Field(ge=0)
