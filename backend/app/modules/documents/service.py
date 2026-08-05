from uuid import UUID
import json
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.database.enums import DocumentStatus, DocumentType, ProcessingJobStatus, ProcessingStage
from app.core.exceptions import ValidationError
from app.modules.auth.schemas import MessageResponse
from app.modules.documents.exceptions import DocumentNotFoundError
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.schemas import (
    DocumentListResponse,
    DocumentMetadataResponse,
    DocumentProcessingJobResponse,
    DocumentSummaryResponse,
    DocumentUploadListResponse,
    DocumentUploadResponse,
    LabMeasurementResponse,
    MedicineResponse,
)
from app.modules.documents.storage import LocalDocumentStorage, SavedFile
from app.modules.family_members.exceptions import FamilyMemberNotFoundError
from app.modules.family_members.repository import FamilyMemberRepository
from app.modules.processing.repository import ProcessingRepository
from app.modules.users.models.models import User
from app.workers.interface import DocumentWorker


class DocumentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        repository: DocumentRepository | None = None,
        family_member_repository: FamilyMemberRepository | None = None,
        storage: LocalDocumentStorage | None = None,
        worker: DocumentWorker | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repository = repository or DocumentRepository(session)
        self._family_members = family_member_repository or FamilyMemberRepository(session)
        self._storage = storage or LocalDocumentStorage(settings)
        self._worker = worker

    async def upload_documents(
        self,
        user: User,
        family_member_id: UUID,
        files: list[UploadFile],
    ) -> DocumentUploadListResponse:
        if not files:
            raise ValidationError("At least one file is required")

        await self._ensure_family_member(user.id, family_member_id)

        uploaded: list[DocumentUploadResponse] = []
        saved_files: list[SavedFile] = []
        document_ids: list[UUID] = []

        try:
            for upload in files:
                saved = await self._storage.save(
                    user_id=user.id,
                    family_member_id=family_member_id,
                    upload=upload,
                )
                saved_files.append(saved)

                document = await self._repository.create(
                    user_id=user.id,
                    family_member_id=family_member_id,
                    original_filename=saved.original_filename,
                    storage_path=saved.storage_path,
                    content_type=saved.content_type,
                    file_size_bytes=saved.file_size_bytes,
                    status=DocumentStatus.PENDING,
                )
                await ProcessingRepository(self._session).create_job(document.id)
                uploaded.append(self._to_response(document))
                document_ids.append(document.id)
        except Exception:
            for saved in saved_files:
                self._storage.delete(saved.storage_path)
            raise

        # Commit before enqueue so the worker session can see the rows.
        await self._session.commit()
        if self._worker is not None:
            for document_id in document_ids:
                await self._worker.enqueue(document_id)

        return DocumentUploadListResponse(items=uploaded, total=len(uploaded))

    async def list_documents(
        self,
        user: User,
        *,
        family_member_id: UUID | None = None,
        document_type: DocumentType | None = None,
        status: DocumentStatus | None = None,
    ) -> DocumentListResponse:
        documents = await self._repository.list_by_user_id(
            user.id,
            family_member_id=family_member_id,
            document_type=document_type,
            status=status,
        )
        return DocumentListResponse(
            items=[self._to_response(document) for document in documents],
            total=len(documents),
        )

    async def get_document(self, user: User, document_id: UUID) -> DocumentUploadResponse:
        document = await self._repository.get_by_id_and_user_id(document_id, user.id)
        if document is None:
            raise DocumentNotFoundError()
        return self._to_response(document)

    async def delete_document(self, user: User, document_id: UUID) -> MessageResponse:
        document = await self._repository.get_by_id_and_user_id(document_id, user.id)
        if document is None:
            raise DocumentNotFoundError()

        storage_path = document.storage_path
        deleted = await self._repository.delete_by_id_and_user_id(document_id, user.id)
        if deleted is None:
            raise DocumentNotFoundError()

        await self._session.commit()
        self._storage.delete(storage_path)
        return MessageResponse(message="Document deleted successfully")

    async def reprocess_document(self, user: User, document_id: UUID) -> DocumentUploadResponse:
        document = await self._repository.get_by_id_and_user_id(document_id, user.id)
        if document is None:
            raise DocumentNotFoundError()

        await self._repository.reset_for_reprocessing(document_id)
        await ProcessingRepository(self._session).create_job(document_id)
        document = await self._repository.get_by_id(document_id)
        if document is not None:
            document.processing_status = ProcessingStage.UPLOADED.value
            document.uploaded_at = datetime.now(UTC)
            document.processed_at = None
        await self._session.commit()

        if self._worker is not None:
            await self._worker.enqueue(document_id)

        return await self.get_document(user, document_id)

    async def _ensure_family_member(self, user_id: UUID, family_member_id: UUID) -> None:
        member = await self._family_members.get_by_id_and_user_id(family_member_id, user_id)
        if member is None:
            raise FamilyMemberNotFoundError()

    def _to_response(self, document: Document) -> DocumentUploadResponse:
        metadata = document.__dict__.get("document_metadata")
        extra = (metadata.extra if metadata is not None else None) or {}
        confidence = extra.get("classification_confidence")
        reasoning = extra.get("classification_reasoning")

        metadata_response = None
        if metadata is not None:
            raw_medicines = metadata.medicines or extra.get("medicines") or []
            medicines: list[MedicineResponse] = []
            if isinstance(raw_medicines, list):
                for item in raw_medicines:
                    if isinstance(item, dict) and item.get("name"):
                        medicines.append(
                            MedicineResponse(
                                name=str(item.get("name")),
                                dosage=item.get("dosage"),
                                frequency=item.get("frequency"),
                                duration=item.get("duration"),
                            )
                        )

            lab_measurements: list[LabMeasurementResponse] = []
            lab_rows = document.__dict__.get("lab_measurements")
            if isinstance(lab_rows, list) and lab_rows:
                for row in lab_rows:
                    lab_measurements.append(
                        LabMeasurementResponse(
                            test_name=row.test_name,
                            value=float(row.value),
                            unit=row.unit,
                            reference_low=(
                                float(row.reference_low)
                                if row.reference_low is not None
                                else None
                            ),
                            reference_high=(
                                float(row.reference_high)
                                if row.reference_high is not None
                                else None
                            ),
                        )
                    )

            metadata_response = DocumentMetadataResponse(
                patient_name=metadata.patient_name,
                doctor_name=metadata.doctor_name,
                hospital_name=metadata.hospital_name,
                document_date=metadata.document_date,
                specialization=metadata.specialization or extra.get("specialization"),
                diagnosis=metadata.diagnosis or extra.get("diagnosis"),
                clinical_summary=metadata.clinical_summary,
                admission_date=metadata.admission_date,
                discharge_date=metadata.discharge_date,
                follow_up=metadata.follow_up,
                medicines=medicines,
                lab_measurements=lab_measurements,
                procedures=list(metadata.procedures or []),
                allergies=list(metadata.allergies or []),
                medical_devices=list(metadata.medical_devices or []),
                vaccinations=list(metadata.vaccinations or []),
            )

        summary_response = self._summary_response(document)
        processing_job = self._processing_job_response(document)

        return DocumentUploadResponse(
            id=document.id,
            family_member_id=document.family_member_id,
            original_filename=document.original_filename,
            content_type=document.content_type,
            file_size_bytes=document.file_size_bytes,
            page_count=document.page_count,
            status=DocumentStatus(document.status),
            processing_status=ProcessingStage(document.processing_status),
            processing_job=processing_job,
            document_type=DocumentType(document.document_type)
            if document.document_type
            else None,
            document_date=document.document_date,
            classification_confidence=float(confidence) if confidence is not None else None,
            classification_reasoning=str(reasoning) if reasoning is not None else None,
            metadata=metadata_response,
            summary=summary_response,
            extracted_text=document.extracted_text,
            processing_error=document.processing_error,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    def _processing_job_response(
        self,
        document: Document,
    ) -> DocumentProcessingJobResponse | None:
        jobs = document.__dict__.get("processing_jobs")
        if not isinstance(jobs, list) or not jobs:
            return None

        latest = max(jobs, key=lambda job: job.created_at)
        return DocumentProcessingJobResponse(
            id=latest.id,
            stage=ProcessingStage(latest.stage),
            status=ProcessingJobStatus(latest.status),
            error_message=latest.error_message,
            retry_count=latest.retry_count,
            next_retry_at=latest.next_retry_at,
            wait_reason=latest.wait_reason,
            started_at=latest.started_at,
            updated_at=latest.updated_at,
        )

    def _summary_response(self, document: Document) -> DocumentSummaryResponse | None:
        ai_summary = document.__dict__.get("ai_summary")
        if ai_summary is None:
            return None

        findings: list[str] = []
        important_dates: list[dict] = []
        highlights: list[str] = list(ai_summary.highlights or [])

        if ai_summary.important_dates:
            important_dates = [
                item
                for item in ai_summary.important_dates
                if isinstance(item, dict) and item.get("date") and item.get("label")
            ]

        raw = ai_summary.key_findings
        if raw:
            try:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    findings = [
                        item for item in (payload.get("findings") or []) if isinstance(item, str)
                    ]
                    if not important_dates:
                        important_dates = [
                            item
                            for item in (payload.get("important_dates") or [])
                            if isinstance(item, dict) and item.get("date") and item.get("label")
                        ]
                elif isinstance(payload, list):
                    findings = [item for item in payload if isinstance(item, str)]
            except json.JSONDecodeError:
                findings = [line.strip() for line in raw.splitlines() if line.strip()]

        return DocumentSummaryResponse(
            short_summary=ai_summary.summary,
            key_findings=findings,
            important_dates=important_dates,
            highlights=highlights,
        )
