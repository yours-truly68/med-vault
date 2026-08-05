from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.database.enums import DocumentStatus, DocumentType, ProcessingJobStatus, ProcessingStage


class MedicineResponse(BaseModel):
    name: str
    dosage: str | None = None
    frequency: str | None = None
    duration: str | None = None


class LabMeasurementResponse(BaseModel):
    test_name: str
    value: float
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None


class DocumentMetadataResponse(BaseModel):
    patient_name: str | None = None
    doctor_name: str | None = None
    hospital_name: str | None = None
    document_date: date | None = None
    specialization: str | None = None
    diagnosis: str | None = None
    clinical_summary: str | None = None
    admission_date: date | None = None
    discharge_date: date | None = None
    follow_up: str | None = None
    medicines: list[MedicineResponse] = Field(default_factory=list)
    lab_measurements: list[LabMeasurementResponse] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    medical_devices: list[str] = Field(default_factory=list)
    vaccinations: list[str] = Field(default_factory=list)


class ImportantDateResponse(BaseModel):
    date: date
    label: str


class DocumentSummaryResponse(BaseModel):
    short_summary: str
    key_findings: list[str] = Field(default_factory=list)
    important_dates: list[ImportantDateResponse] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)

    @field_validator("highlights", mode="before")
    @classmethod
    def coerce_highlights(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            lines = [line.strip() for line in value.splitlines() if line.strip()]
            return [cls._clean_highlight_item(l) for l in lines if cls._clean_highlight_item(l)]
        if isinstance(value, list):
            results: list[str] = []
            for item in value:
                cleaned = cls._clean_highlight_item(item)
                if cleaned:
                    results.append(cleaned)
            return results
        return []

    @classmethod
    def _clean_highlight_item(cls, item: Any) -> str | None:
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


class DocumentProcessingJobResponse(BaseModel):
    id: UUID
    stage: ProcessingStage
    status: ProcessingJobStatus
    error_message: str | None = None
    retry_count: int = 0
    next_retry_at: datetime | None = None
    wait_reason: str | None = None
    started_at: datetime | None = None
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_member_id: UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    page_count: int | None = None
    status: DocumentStatus
    indexing_status: str = "not_started"
    processing_status: ProcessingStage
    processing_job: DocumentProcessingJobResponse | None = None
    document_type: DocumentType | None = None
    document_date: date | None = None
    classification_confidence: float | None = None
    classification_reasoning: str | None = None
    metadata: DocumentMetadataResponse | None = None
    summary: DocumentSummaryResponse | None = None
    extracted_text: str | None = None
    processing_error: str | None = None
    indexing_error: str | None = None
    stage_timings: dict[str, Any] | None = None
    uploaded_at: datetime | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DocumentUploadListResponse(BaseModel):
    items: list[DocumentUploadResponse]
    total: int = Field(ge=0)


class DocumentListResponse(BaseModel):
    items: list[DocumentUploadResponse]
    total: int = Field(ge=0)
