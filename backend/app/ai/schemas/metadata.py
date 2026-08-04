"""Pydantic models for AI metadata extraction structured output."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MedicineItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=255)
    dosage: str | None = Field(default=None, max_length=128)
    frequency: str | None = Field(default=None, max_length=128)
    duration: str | None = Field(default=None, max_length=128)

    @field_validator("name", "dosage", "frequency", "duration", mode="before")
    @classmethod
    def blank_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in {"null", "none", "n/a", "na"}:
                return None
            return stripped
        return value


class ExtractedDocumentMetadata(BaseModel):
    """Structured metadata returned by the extraction LLM."""

    model_config = ConfigDict(extra="ignore")

    patient_name: str | None = Field(default=None, max_length=255)
    doctor_name: str | None = Field(default=None, max_length=255)
    hospital_name: str | None = Field(default=None, max_length=255)
    document_date: date | None = None
    specialization: str | None = Field(default=None, max_length=255)
    diagnosis: str | None = Field(default=None, max_length=2000)
    medicines: list[MedicineItem] = Field(default_factory=list)

    @field_validator(
        "patient_name",
        "doctor_name",
        "hospital_name",
        "specialization",
        "diagnosis",
        mode="before",
    )
    @classmethod
    def blank_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped or stripped.lower() in {"null", "none", "n/a", "na"}:
                return None
            return stripped
        return value

    @field_validator("document_date", mode="before")
    @classmethod
    def parse_document_date(cls, value: Any) -> Any:
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
            # Prefer ISO; accept common day-first / month-first variants lightly.
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(stripped[:10], fmt).date()
                except ValueError:
                    continue
            try:
                return date.fromisoformat(stripped[:10])
            except ValueError:
                return None
        return None

    @field_validator("medicines", mode="before")
    @classmethod
    def coerce_medicines(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, list):
            cleaned: list[Any] = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    cleaned.append({"name": item.strip()})
                elif isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        cleaned.append(item)
            return cleaned
        return []
