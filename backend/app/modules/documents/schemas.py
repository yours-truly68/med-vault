from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.database.enums import DocumentStatus, DocumentType


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


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    family_member_id: UUID
    original_filename: str
    content_type: str
    file_size_bytes: int
    page_count: int | None = None
    status: DocumentStatus
    document_type: DocumentType | None = None
    document_date: date | None = None
    classification_confidence: float | None = None
    classification_reasoning: str | None = None
    metadata: DocumentMetadataResponse | None = None
    summary: DocumentSummaryResponse | None = None
    extracted_text: str | None = None
    processing_error: str | None = None
    created_at: datetime
    updated_at: datetime


class DocumentUploadListResponse(BaseModel):
    items: list[DocumentUploadResponse]
    total: int = Field(ge=0)


class DocumentListResponse(BaseModel):
    items: list[DocumentUploadResponse]
    total: int = Field(ge=0)
