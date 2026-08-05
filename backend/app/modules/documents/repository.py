from uuid import UUID
from datetime import date, datetime, UTC
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.embeddings.pg_vector_store import PgVectorStore
from app.core.database.enums import DocumentStatus, DocumentType, ProcessingStage
from app.modules.documents.models import (
    AISummary,
    Document,
    DocumentMetadata,
    Embedding,
    LabMeasurement,
    TimelineEvent,
)


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: UUID,
        family_member_id: UUID,
        original_filename: str,
        storage_path: str,
        content_type: str,
        file_size_bytes: int,
        status: DocumentStatus = DocumentStatus.PENDING,
    ) -> Document:
        document = Document(
            user_id=user_id,
            family_member_id=family_member_id,
            original_filename=original_filename,
            storage_path=storage_path,
            content_type=content_type,
            file_size_bytes=file_size_bytes,
            status=status.value,
            processing_status=ProcessingStage.UPLOADED.value,
            uploaded_at=datetime.now(UTC),
        )
        self._session.add(document)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def list_by_user_id(
        self,
        user_id: UUID,
        *,
        family_member_id: UUID | None = None,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
    ) -> list[Document]:
        stmt = (
            select(Document)
            .options(
                selectinload(Document.document_metadata),
                selectinload(Document.ai_summary),
                selectinload(Document.lab_measurements),
                selectinload(Document.processing_jobs),
            )
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
        )
        if family_member_id is not None:
            stmt = stmt.where(Document.family_member_id == family_member_id)
        if document_type is not None:
            stmt = stmt.where(Document.document_type == document_type.value)
        if status is not None:
            stmt = stmt.where(Document.status == status.value)

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, document_id: UUID) -> Document | None:
        result = await self._session.execute(
            select(Document)
            .options(
                selectinload(Document.document_metadata),
                selectinload(Document.ai_summary),
                selectinload(Document.lab_measurements),
                selectinload(Document.processing_jobs),
            )
            .where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, document_id: UUID, status: DocumentStatus) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.status = status.value
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def set_extracted_text(
        self,
        document_id: UUID,
        *,
        extracted_text: str,
        status: DocumentStatus = DocumentStatus.COMPLETED,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.extracted_text = extracted_text
        document.status = status.value
        document.processing_error = None
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def set_processing_failed(
        self,
        document_id: UUID,
        error_message: str,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.status = DocumentStatus.FAILED.value
        document.processing_error = error_message[:4000]
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def reset_for_reprocessing(self, document_id: UUID) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.status = DocumentStatus.PENDING.value
        document.processing_status = ProcessingStage.UPLOADED.value
        document.processing_error = None
        document.document_type = None
        document.processed_at = None
        await PgVectorStore(self._session).delete(document_id)
        await self._delete_derived_rows(document_id)
        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def _delete_derived_rows(self, document_id: UUID) -> None:
        for model in (LabMeasurement, TimelineEvent):
            result = await self._session.execute(
                select(model).where(model.document_id == document_id)
            )
            for row in result.scalars().all():
                await self._session.delete(row)

    async def set_processing_result(
        self,
        document_id: UUID,
        *,
        extracted_text: str,
        page_count: int | None = None,
        document_type: DocumentType,
        confidence: float,
        reasoning: str,
        model_name: str,
        patient_name: str | None = None,
        doctor_name: str | None = None,
        hospital_name: str | None = None,
        document_date: date | None = None,
        specialization: str | None = None,
        diagnosis: str | None = None,
        clinical_summary: str | None = None,
        admission_date: date | None = None,
        discharge_date: date | None = None,
        follow_up: str | None = None,
        medicines: list[dict] | None = None,
        lab_measurements: list[dict] | None = None,
        procedures: list[str] | None = None,
        allergies: list[str] | None = None,
        medical_devices: list[str] | None = None,
        vaccinations: list[str] | None = None,
        metadata_model_name: str | None = None,
        short_summary: str | None = None,
        key_findings: list[str] | None = None,
        important_dates: list[dict] | None = None,
        highlights: list[str] | None = None,
        summary_model_name: str | None = None,
        timeline_events: list[dict[str, Any]] | None = None,
        embedding_vector: list[float] | None = None,
        embedding_model_name: str | None = None,
        embedding_dimensions: int | None = None,
        status: DocumentStatus = DocumentStatus.READY,
        indexing_status: str = "not_started",
        stage_timings: dict[str, Any] | None = None,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.extracted_text = extracted_text
        document.document_type = document_type.value
        document.document_date = document_date
        document.status = status.value
        document.indexing_status = indexing_status
        if stage_timings is not None:
            document.stage_timings = stage_timings
        document.processing_error = None

        metadata = await self._get_or_create_metadata(document_id)
        metadata.document_type = document_type.value
        metadata.patient_name = patient_name
        metadata.doctor_name = doctor_name
        metadata.hospital_name = hospital_name
        metadata.document_date = document_date
        metadata.specialization = specialization
        metadata.diagnosis = diagnosis
        metadata.clinical_summary = clinical_summary
        metadata.admission_date = admission_date
        metadata.discharge_date = discharge_date
        metadata.follow_up = follow_up
        metadata.medicines = medicines or []
        metadata.procedures = procedures or []
        metadata.allergies = allergies or []
        metadata.medical_devices = medical_devices or []
        metadata.vaccinations = vaccinations or []

        extra = dict(metadata.extra or {})
        extra.update(
            {
                "classification_confidence": confidence,
                "classification_reasoning": reasoning,
                "classification_model": model_name,
                "metadata_model": metadata_model_name,
            }
        )
        metadata.extra = extra

        await self._delete_derived_rows(document_id)

        measured_at = document_date or admission_date
        for item in lab_measurements or []:
            self._session.add(
                LabMeasurement(
                    document_id=document_id,
                    user_id=document.user_id,
                    family_member_id=document.family_member_id,
                    test_name=str(item["test_name"]),
                    value=float(item["value"]),
                    unit=item.get("unit"),
                    reference_low=item.get("reference_low"),
                    reference_high=item.get("reference_high"),
                    measured_at=measured_at,
                )
            )

        for event in timeline_events or []:
            self._session.add(
                TimelineEvent(
                    document_id=document_id,
                    user_id=document.user_id,
                    family_member_id=document.family_member_id,
                    event_date=event["event_date"],
                    event_type=event["event_type"],
                    title=event["title"],
                    description=event.get("description"),
                    source_field=event.get("source_field"),
                )
            )

        if short_summary:
            await self._upsert_summary(
                document_id,
                summary=short_summary,
                key_findings=key_findings or [],
                important_dates=important_dates or [],
                highlights=highlights or [],
                model_name=summary_model_name,
            )

        if embedding_vector is not None and embedding_model_name and embedding_dimensions:
            await PgVectorStore(self._session).upsert(
                document_id,
                embedding=embedding_vector,
                model_name=embedding_model_name,
                dimensions=embedding_dimensions,
            )

        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def _get_or_create_metadata(self, document_id: UUID) -> DocumentMetadata:
        result = await self._session.execute(
            select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        )
        metadata = result.scalar_one_or_none()
        if metadata is not None:
            return metadata

        metadata = DocumentMetadata(document_id=document_id)
        self._session.add(metadata)
        await self._session.flush()
        return metadata

    async def _upsert_summary(
        self,
        document_id: UUID,
        *,
        summary: str,
        key_findings: list[str],
        important_dates: list[dict],
        highlights: list[str],
        model_name: str | None,
    ) -> AISummary:
        result = await self._session.execute(
            select(AISummary).where(AISummary.document_id == document_id)
        )
        row = result.scalar_one_or_none()
        findings_payload = json.dumps(key_findings, ensure_ascii=True)

        if row is None:
            row = AISummary(
                document_id=document_id,
                summary=summary,
                key_findings=findings_payload,
                important_dates=important_dates,
                highlights=highlights,
                model_name=model_name,
            )
            self._session.add(row)
        else:
            row.summary = summary
            row.key_findings = findings_payload
            row.important_dates = important_dates
            row.highlights = highlights
            row.model_name = model_name

        await self._session.flush()
        return row

    async def get_by_id_and_user_id(self, document_id: UUID, user_id: UUID) -> Document | None:
        result = await self._session.execute(
            select(Document)
            .options(
                selectinload(Document.document_metadata),
                selectinload(Document.ai_summary),
                selectinload(Document.lab_measurements),
                selectinload(Document.processing_jobs),
            )
            .where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def set_processing_rejected(
        self,
        document_id: UUID,
        *,
        extracted_text: str,
        confidence: float,
        reasoning: str,
        model_name: str,
        error_message: str,
    ) -> Document | None:
        document = await self.get_by_id(document_id)
        if document is None:
            return None

        document.extracted_text = extracted_text
        document.document_type = DocumentType.UNRELATED.value
        document.status = DocumentStatus.REJECTED.value
        document.processing_error = error_message[:4000]

        metadata = await self._get_or_create_metadata(document_id)
        metadata.document_type = DocumentType.UNRELATED.value
        extra = dict(metadata.extra or {})
        extra.update(
            {
                "classification_confidence": confidence,
                "classification_reasoning": reasoning,
                "classification_model": model_name,
                "rejected": True,
            }
        )
        metadata.extra = extra

        # Ensure no stale embeddings remain if this was a reprocess.
        await PgVectorStore(self._session).delete(document_id)
        await self._delete_derived_rows(document_id)

        await self._session.flush()
        await self._session.refresh(document)
        return document

    async def delete_by_id_and_user_id(
        self,
        document_id: UUID,
        user_id: UUID,
    ) -> Document | None:
        document = await self.get_by_id_and_user_id(document_id, user_id)
        if document is None:
            return None

        await PgVectorStore(self._session).delete(document_id)
        await self._session.delete(document)
        await self._session.flush()
        return document
