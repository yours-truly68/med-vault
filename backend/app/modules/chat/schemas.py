from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.database.enums import DocumentType


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)
    min_score: float | None = Field(default=None, ge=0.0, le=1.0)
    family_member_id: UUID | None = None


class ChatCitation(BaseModel):
    document_id: UUID
    original_filename: str
    document_type: DocumentType | None = None
    document_date: date | None = None
    family_member_id: UUID
    score: float
    page: int | None = None
    excerpt: str | None = None
    summary: str | None = None


class ChatSupportingDetails(BaseModel):
    patient: str | None = None
    doctor: str | None = None
    hospital: str | None = None
    diagnosis: str | None = None
    medicines: list[str] = Field(default_factory=list)
    lab_values: list[str] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    follow_up: str | None = None


class ChatTimelineEntry(BaseModel):
    date: str | None = None
    label: str | None = None
    detail: str | None = None


class ChatAskResponse(BaseModel):
    question: str
    answer: str
    insufficient_context: bool
    citations: list[ChatCitation]
    supporting_details: ChatSupportingDetails | None = None
    timeline: list[ChatTimelineEntry] = Field(default_factory=list)
    model_name: str | None = None
