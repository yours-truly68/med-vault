from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.database.enums import TimelineEventType


class TimelineEventResponse(BaseModel):
    id: UUID
    document_id: UUID
    family_member_id: UUID
    event_date: date
    event_type: TimelineEventType
    title: str
    description: str | None = None
    source_field: str | None = None
    document_type: str | None = None
    original_filename: str | None = None


class TimelineListResponse(BaseModel):
    items: list[TimelineEventResponse]
    total: int = Field(ge=0)
