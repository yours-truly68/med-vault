"""Pydantic models for RAG grounded responses."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RagCitation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: UUID
    page: int | None = None


class SupportingLabValue(BaseModel):
    model_config = ConfigDict(extra="ignore")

    test_name: str
    value: float | str | None = None
    unit: str | None = None
    reference_low: float | str | None = None
    reference_high: float | str | None = None

    @field_validator("test_name", mode="before")
    @classmethod
    def coerce_test_name(cls, value: Any) -> str:
        if value is None:
            return "Lab Result"
        return str(value).strip() or "Lab Result"


class RagSupportingDetails(BaseModel):
    model_config = ConfigDict(extra="ignore")

    patient: str | None = None
    doctor: str | None = None
    hospital: str | None = None
    diagnosis: str | None = None
    medicines: list[str] = Field(default_factory=list)
    lab_values: list[SupportingLabValue] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    follow_up: str | None = None

    @field_validator("lab_values", mode="before")
    @classmethod
    def coerce_lab_values(cls, value: Any) -> list[Any]:
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]

        cleaned: list[Any] = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                text = item.strip()
                if text:
                    cleaned.append({"test_name": text})
            elif isinstance(item, dict):
                raw = dict(item)
                if "test_name" not in raw or not raw["test_name"]:
                    test_name = raw.get("name") or raw.get("label") or raw.get("test") or "Lab Result"
                    raw["test_name"] = str(test_name)
                cleaned.append(raw)
            elif isinstance(item, (int, float)):
                cleaned.append({"test_name": f"Measurement: {item}"})
            else:
                cleaned.append({"test_name": str(item)})
        return cleaned


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
