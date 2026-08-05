"""Unit tests for timeline building logic and metadata integration."""

from datetime import date
from uuid import uuid4

import app.core.database.models  # noqa: F401
from app.ai.schemas.metadata import ExtractedDocumentMetadata, MedicineItem, LabMeasurementItem
from app.ai.schemas.summary import DocumentSummary
from app.core.database.enums import DocumentStatus, TimelineEventType
from app.modules.documents.models import Document
from app.modules.processing.timeline import build_timeline_events


def test_build_timeline_events_with_extracted_metadata() -> None:
    document = Document(
        id=uuid4(),
        user_id=uuid4(),
        family_member_id=uuid4(),
        original_filename="lab_report.pdf",
        storage_path="docs/lab_report.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        status=DocumentStatus.READY.value,
        document_date=date(2026, 1, 15),
    )

    metadata = ExtractedDocumentMetadata(
        patient_name="John Doe",
        doctor_name="Dr. Smith",
        hospital_name="City Hospital",
        document_date=date(2026, 1, 15),
        diagnosis="Type 2 Diabetes Mellitus",
        summary="Patient presents with elevated HbA1c levels.",
        admission_date=date(2026, 1, 10),
        discharge_date=date(2026, 1, 12),
        medicines=[
            MedicineItem(name="Metformin", dosage="500mg", frequency="Twice daily", duration="30 days")
        ],
        lab_measurements=[
            LabMeasurementItem(test_name="HbA1c", value=8.2, unit="%")
        ],
        procedures=["Blood Draw"],
        allergies=["Penicillin"],
        follow_up="Consult endocrinologist in 2 weeks",
    )

    summary = DocumentSummary(
        short_summary="Type 2 Diabetes follow up report.",
        key_findings=["Elevated HbA1c"],
        highlights=["Started Metformin"],
    )

    events = build_timeline_events(document, metadata, summary)
    assert len(events) > 0

    diagnosis_events = [e for e in events if e.event_type == TimelineEventType.DIAGNOSIS]
    assert len(diagnosis_events) == 1
    assert diagnosis_events[0].title == "Type 2 Diabetes Mellitus"
    assert diagnosis_events[0].description == "Patient presents with elevated HbA1c levels."
