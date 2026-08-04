"""Pydantic models for AI document summarization structured output."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class ImportantDate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: date
    label: str = Field(min_length=1, max_length=255)

    @field_validator("label", mode="before")
    @classmethod
    def clean_label(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in {"null", "none", "n/a", "na"}:
                return None
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(stripped[:10], fmt).date()
                except ValueError:
                    continue
            try:
                return date.fromisoformat(stripped[:10])
            except ValueError:
                return None
        return value


class DocumentSummary(BaseModel):
    """Structured summary returned by the summarization LLM."""

    model_config = ConfigDict(extra="ignore")

    short_summary: str = Field(min_length=1, max_length=4000)
    key_findings: list[str] = Field(default_factory=list)
    important_dates: list[ImportantDate] = Field(default_factory=list)

    @field_validator("short_summary", mode="before")
    @classmethod
    def clean_summary(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("key_findings", mode="before")
    @classmethod
    def coerce_findings(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            lines = [line.strip(" -\t") for line in value.splitlines()]
            return [line for line in lines if line]
        if isinstance(value, list):
            findings: list[str] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    findings.append(item.strip()[:1000])
            return findings
        return []

    @field_validator("important_dates", mode="before")
    @classmethod
    def coerce_dates(cls, value: Any) -> Any:
        if value is None:
            return []
        if not isinstance(value, list):
            return []
        cleaned: list[Any] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            try:
                cleaned.append(ImportantDate.model_validate(item).model_dump(mode="json"))
            except ValidationError:
                continue
        return cleaned
