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
    highlights: list[str] = Field(default_factory=list)

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

    @field_validator("highlights", mode="before")
    @classmethod
    def coerce_highlights(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            lines = [line.strip() for line in value.splitlines() if line.strip()]
            return [cls._clean_single_highlight(l) for l in lines if cls._clean_single_highlight(l)]
        if isinstance(value, list):
            results: list[str] = []
            for item in value:
                cleaned = cls._clean_single_highlight(item)
                if cleaned:
                    results.append(cleaned)
            return results
        return []

    @classmethod
    def _clean_single_highlight(cls, item: Any) -> str | None:
        if item is None:
            return None
        if isinstance(item, str):
            trimmed = item.strip()
            if not trimmed:
                return None
            if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("{'") and trimmed.endswith("'}")):
                try:
                    import json
                    parsed = json.loads(trimmed)
                    if isinstance(parsed, dict):
                        val = parsed.get("item") or parsed.get("highlight") or parsed.get("text") or parsed.get("finding")
                        if val and isinstance(val, str):
                            return val.strip()
                except Exception:
                    pass
                import re
                m = re.search(r"['\"]item['\"]:\s*['\"]([^'\"]+)['\"]", trimmed)
                if m:
                    return m.group(1).strip()
            return trimmed
        if isinstance(item, dict):
            val = item.get("item") or item.get("highlight") or item.get("text") or item.get("finding")
            if val and isinstance(val, str):
                return val.strip()
            if item:
                first_val = next(iter(item.values()))
                if isinstance(first_val, str):
                    return first_val.strip()
        val_str = str(item).strip()
        return val_str if val_str else None
