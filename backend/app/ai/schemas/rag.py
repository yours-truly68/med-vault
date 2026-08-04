"""Pydantic models for RAG grounded responses."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    answer: str = Field(min_length=1, max_length=8000)
    cited_document_ids: list[UUID] = Field(default_factory=list)
    insufficient_context: bool = False

    @field_validator("answer", mode="before")
    @classmethod
    def clean_answer(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

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
