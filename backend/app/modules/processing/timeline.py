"""Build timeline events from extracted metadata and summaries."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.ai.schemas.metadata import ExtractedDocumentMetadata
from app.ai.schemas.summary import DocumentSummary
from app.core.database.enums import DocumentType, TimelineEventType
from app.modules.documents.models import Document


@dataclass(frozen=True)
class TimelineEventDraft:
    event_date: date
    event_type: TimelineEventType
    title: str
    description: str | None = None
    source_field: str | None = None


def _resolve_date(*values: date | None) -> date | None:
    for value in values:
        if value is not None:
            return value
    return None


def build_timeline_events(
    document: Document,
    metadata: ExtractedDocumentMetadata | None,
    summary: DocumentSummary | None,
) -> list[TimelineEventDraft]:
    events: list[TimelineEventDraft] = []
    base_date = _resolve_date(
        document.document_date,
        metadata.document_date if metadata else None,
    )

    if base_date is not None:
        events.append(
            TimelineEventDraft(
                event_date=base_date,
                event_type=TimelineEventType.DOCUMENT,
                title=document.original_filename,
                description=summary.short_summary if summary else None,
                source_field="document_date",
            )
        )

    if metadata is None:
        return events

    if metadata.admission_date:
        events.append(
            TimelineEventDraft(
                event_date=metadata.admission_date,
                event_type=TimelineEventType.ADMISSION,
                title="Hospital admission",
                description=metadata.hospital_name,
                source_field="admission_date",
            )
        )

    if metadata.discharge_date:
        events.append(
            TimelineEventDraft(
                event_date=metadata.discharge_date,
                event_type=TimelineEventType.DISCHARGE,
                title="Hospital discharge",
                description=metadata.hospital_name,
                source_field="discharge_date",
            )
        )

    if metadata.diagnosis:
        event_date = base_date or metadata.admission_date or metadata.discharge_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.DIAGNOSIS,
                    title=metadata.diagnosis,
                    description=metadata.summary,
                    source_field="diagnosis",
                )
            )

    for procedure in metadata.procedures:
        event_date = base_date or metadata.admission_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.PROCEDURE,
                    title=procedure,
                    source_field="procedures",
                )
            )

    for medicine in metadata.medicines:
        event_date = base_date or metadata.admission_date
        if event_date is not None:
            detail = ", ".join(
                part
                for part in (medicine.dosage, medicine.frequency, medicine.duration)
                if part
            )
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.MEDICATION,
                    title=medicine.name,
                    description=detail or None,
                    source_field="medicines",
                )
            )

    for lab in metadata.lab_measurements:
        event_date = base_date or metadata.admission_date
        if event_date is not None:
            unit = f" {lab.unit}" if lab.unit else ""
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.LAB_RESULT,
                    title=lab.test_name,
                    description=f"{lab.value}{unit}",
                    source_field="lab_measurements",
                )
            )

    for allergy in metadata.allergies:
        event_date = base_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.ALLERGY,
                    title=allergy,
                    source_field="allergies",
                )
            )

    for device in metadata.medical_devices:
        event_date = base_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.DEVICE,
                    title=device,
                    source_field="medical_devices",
                )
            )

    for vaccination in metadata.vaccinations:
        event_date = base_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.VACCINATION,
                    title=vaccination,
                    source_field="vaccinations",
                )
            )

    if metadata.follow_up:
        event_date = base_date
        if event_date is not None:
            events.append(
                TimelineEventDraft(
                    event_date=event_date,
                    event_type=TimelineEventType.FOLLOW_UP,
                    title="Follow-up",
                    description=metadata.follow_up,
                    source_field="follow_up",
                )
            )

    if document.document_type == DocumentType.IMAGING_REPORT.value and base_date is not None:
        events.append(
            TimelineEventDraft(
                event_date=base_date,
                event_type=TimelineEventType.IMAGING,
                title="Imaging report",
                description=summary.short_summary if summary else None,
                source_field="document_type",
            )
        )

    if summary is not None:
        for item in summary.important_dates:
            events.append(
                TimelineEventDraft(
                    event_date=item.date,
                    event_type=TimelineEventType.VISIT,
                    title=item.label,
                    source_field="important_dates",
                )
            )

    deduped: list[TimelineEventDraft] = []
    seen: set[tuple[date, str, str]] = set()
    for event in events:
        key = (event.event_date, event.event_type.value, event.title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(event)

    deduped.sort(key=lambda item: item.event_date, reverse=True)
    return deduped
