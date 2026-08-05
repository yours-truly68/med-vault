"""Pydantic models for RAG grounded responses."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RagCitation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: UUID
    page: int | None = None


class RagSupportingDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    patient: str | None = None
    doctor: str | None = None
    hospital: str | None = None
    diagnosis: str | None = None
    medicines: list[str] = Field(default_factory=list)
    lab_values: list[str] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    follow_up: str | None = None


class RagTimelineEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str | None = None
    label: str | None = None
    detail: str | None = None


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(min_length=1, max_length=8000)
    supporting_details: RagSupportingDetails | None = None
    timeline: list[RagTimelineEntry] = Field(default_factory=list)
    citations: list[RagCitation] = Field(default_factory=list)
    cited_document_ids: list[UUID] = Field(default_factory=list)
    insufficient_context: bool = False

    @field_validator("answer", mode="before")
    @classmethod
    def clean_answer(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("citations", mode="before")
    @classmethod
    def coerce_citations(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        cleaned: list[dict[str, Any]] = []
        for item in value:
            if isinstance(item, dict) and item.get("document_id"):
                cleaned.append(item)
        return cleaned

    @field_validator("cited_document_ids", mode="before")
    @classmethod
    def coerce_ids(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        cleaned: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                cleaned.append(text)
        return cleaned
