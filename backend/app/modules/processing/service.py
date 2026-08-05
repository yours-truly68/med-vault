"""Processing service: orchestrates jobs, pause/resume, and persistence."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.classifier import ClassificationError
from app.ai.embeddings.embeddings import (
    DocumentEmbeddingResult,
    EmbeddingError,
)
from app.ai.errors import RateLimitError
from app.ai.metadata import MetadataExtractionError
from app.ai.ocr import OcrError, OcrResult
from app.ai.summarizer import SummarizationError
from app.core.config.settings import Settings
from app.core.database.enums import (
    DocumentStatus,
    ProcessingJobStatus,
    ProcessingStage,
)
from app.core.database.session import Database
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.processing.exceptions import ProcessingJobNotFoundError, ProcessingPausedError
from app.modules.processing.models import ProcessingJob
from app.modules.processing.pipeline import PIPELINE_STAGES, ProcessingPipeline, ProcessingState
from app.modules.processing.repository import ProcessingRepository
from app.modules.processing.schemas import (
    ProcessingControlResponse,
    ProcessingJobResponse,
    ProcessingStatusResponse,
)
from app.modules.users.models.models import User

logger = logging.getLogger(__name__)

PROCESSABLE_DOCUMENT_STATUSES = frozenset({
    DocumentStatus.PENDING.value,
    DocumentStatus.PROCESSING.value,
})


class ProcessingService:
    def __init__(
        self,
        session: AsyncSession | None,
        settings: Settings,
        *,
        database: Database | None = None,
        pipeline: ProcessingPipeline | None = None,
        repository: ProcessingRepository | None = None,
    ) -> None:
        self._session = session
        self._database = database
        self._settings = settings
        self._pipeline = pipeline or ProcessingPipeline(settings)
        self._repository = repository

    def _repo(self, session: AsyncSession) -> ProcessingRepository:
        return self._repository or ProcessingRepository(session)

    async def create_job_for_document(self, document_id: UUID) -> ProcessingJob:
        if self._session is None:
            raise RuntimeError("Database session is required to create a processing job")

        repo = self._repo(self._session)
        job = await repo.create_job(document_id)

        document_repo = DocumentRepository(self._session)
        document = await document_repo.get_by_id(document_id)
        if document is not None:
            document.processing_status = ProcessingStage.UPLOADED.value
            document.uploaded_at = document.uploaded_at or datetime.now(UTC)

        return job

    async def get_job(self, user: User, job_id: UUID) -> ProcessingJobResponse:
        if self._session is None:
            raise RuntimeError("Database session is required")

        job = await self._get_owned_job(user, job_id)
        return ProcessingJobResponse.model_validate(job)

    async def get_status(self, user: User) -> ProcessingStatusResponse:
        if self._session is None:
            raise RuntimeError("Database session is required")

        repo = self._repo(self._session)
        globally_paused = await repo.is_globally_paused()
        counts = await repo.count_jobs_by_status()

        return ProcessingStatusResponse(
            globally_paused=globally_paused,
            active_jobs=counts.get(ProcessingJobStatus.RUNNING.value, 0),
            paused_jobs=counts.get(ProcessingJobStatus.PAUSED.value, 0),
            pending_jobs=counts.get(ProcessingJobStatus.PENDING.value, 0),
            rate_limited_jobs=await repo.count_rate_limited_jobs(),
        )

    async def pause_global(self, user: User) -> ProcessingControlResponse:
        _ = user
        if self._session is None:
            raise RuntimeError("Database session is required")

        await self._repo(self._session).set_global_pause(True)
        await self._session.commit()
        return ProcessingControlResponse(
            globally_paused=True,
            message="Document processing paused globally.",
        )

    async def resume_global(self, user: User) -> ProcessingControlResponse:
        _ = user
        if self._session is None:
            raise RuntimeError("Database session is required")

        await self._repo(self._session).set_global_pause(False)
        await self._session.commit()
        return ProcessingControlResponse(
            globally_paused=False,
            message="Document processing resumed globally.",
        )

    async def pause_job(self, user: User, job_id: UUID) -> ProcessingJobResponse:
        if self._session is None:
            raise RuntimeError("Database session is required")

        await self._get_owned_job(user, job_id)
        job = await self._repo(self._session).pause_job(job_id)
        if job is None:
            raise ProcessingJobNotFoundError()
        await self._session.commit()
        return ProcessingJobResponse.model_validate(job)

    async def resume_job(self, user: User, job_id: UUID) -> ProcessingJobResponse:
        if self._session is None:
            raise RuntimeError("Database session is required")

        job = await self._get_owned_job(user, job_id)
        resumed = await self._repo(self._session).resume_job(job.id)
        if resumed is None:
            raise ProcessingJobNotFoundError()
        await self._session.commit()
        return ProcessingJobResponse.model_validate(resumed)

    async def process_document(
        self,
        document_id: UUID,
        *,
        embeddings_only: bool = False,
    ) -> None:
        """Entry point used by background workers (BackgroundTasks, Celery, ARQ, etc.)."""
        if self._database is None:
            raise RuntimeError("Database handle is required for background processing")

        async with self._database.session_scope() as session:
            document_repo = DocumentRepository(session)
            processing_repo = self._repo(session)

            document = await document_repo.get_by_id(document_id)
            if document is None:
                logger.warning("Document %s not found; skipping processing", document_id)
                return

            if not embeddings_only and document.status not in PROCESSABLE_DOCUMENT_STATUSES:
                logger.info(
                    "Document %s has status %r; skipping processing",
                    document_id,
                    document.status,
                )
                return

            job = await processing_repo.get_latest_job_for_document(document_id)
            if job is None:
                job = await processing_repo.create_job(document_id)

            if job.status == ProcessingJobStatus.PAUSED.value:
                logger.info("Processing job %s is paused; skipping", job.id)
                return

            if await processing_repo.is_globally_paused():
                await processing_repo.mark_job_paused(job.id)
                await session.commit()
                logger.info("Global processing pause active; job %s paused", job.id)
                return

            if not embeddings_only:
                await document_repo.update_status(document_id, DocumentStatus.PROCESSING)
                document.processing_status = ProcessingStage.UPLOADED.value
                await processing_repo.mark_job_running(job.id, stage=ProcessingStage.UPLOADED)
                await session.commit()

        if embeddings_only:
            state = await self._load_state_for_embedding_retry(document_id, job.id)
            if state is None:
                logger.warning(
                    "Document %s is not ready for embedding retry; skipping",
                    document_id,
                )
                return
            stages = (ProcessingStage.EMBEDDINGS,)
        else:
            state = ProcessingState(document=document, job_id=job.id)
            stages = PIPELINE_STAGES

        try:
            for stage in stages:
                await self._ensure_can_continue(document_id, job.id)

                async with self._database.session_scope() as session:
                    processing_repo = self._repo(session)
                    await processing_repo.mark_job_running(job.id, stage=stage)
                    document_repo = DocumentRepository(session)
                    doc = await document_repo.get_by_id(document_id)
                    if doc is not None:
                        doc.processing_status = stage.value
                    await session.commit()

                state = await self._pipeline.run_stage(stage, state)

                if stage == ProcessingStage.CLASSIFICATION and state.rejected:
                    await self._persist_rejected(document_id, job.id, state)
                    return

            await self._persist_success(document_id, job.id, state, embeddings_only=embeddings_only)
        except ProcessingPausedError:
            logger.info("Processing paused for document %s", document_id)
        except RateLimitError as exc:
            logger.warning("Rate limit hit for document %s: %s", document_id, exc)
            stage = self._infer_rate_limited_stage(state, embeddings_only=embeddings_only)
            await self._persist_rate_limited(
                document_id,
                job.id,
                state,
                stage=stage,
                error=exc,
                embeddings_only=embeddings_only,
            )
        except (
            OcrError,
            ClassificationError,
            MetadataExtractionError,
            SummarizationError,
            EmbeddingError,
            FileNotFoundError,
            ValueError,
        ) as exc:
            logger.exception("Document %s processing failed", document_id)
            await self._persist_failure(document_id, job.id, str(exc))
        except Exception as exc:
            logger.exception("Document %s processing failed unexpectedly", document_id)
            await self._persist_failure(document_id, job.id, str(exc))

    async def retry_deferred_jobs(self) -> int:
        """Re-enqueue jobs whose rate-limit cooldown has elapsed."""
        if self._database is None:
            return 0

        requeued = 0
        async with self._database.session_scope() as session:
            processing_repo = self._repo(session)
            jobs = await processing_repo.list_jobs_ready_for_retry()
            for job in jobs:
                await processing_repo.requeue_job_for_retry(job.id)
                requeued += 1
            await session.commit()

        return requeued

    async def reprocess_document(self, document_id: UUID) -> None:
        if self._database is None:
            raise RuntimeError("Database handle is required for background processing")

        async with self._database.session_scope() as session:
            await DocumentRepository(session).reset_for_reprocessing(document_id)
            job = await self._repo(session).create_job(document_id)
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is not None:
                document.processing_status = ProcessingStage.UPLOADED.value
                document.uploaded_at = datetime.now(UTC)
                document.processed_at = None
            await session.commit()

        await self.process_document(document_id)

    async def _ensure_can_continue(self, document_id: UUID, job_id: UUID) -> None:
        if self._database is None:
            return

        async with self._database.session_scope() as session:
            processing_repo = self._repo(session)
            if await processing_repo.is_globally_paused():
                await processing_repo.mark_job_paused(job_id)
                await session.commit()
                raise ProcessingPausedError("Global processing is paused")

            job = await processing_repo.get_job(job_id)
            if job is None:
                raise ProcessingJobNotFoundError()
            if job.status == ProcessingJobStatus.PAUSED.value:
                await session.commit()
                raise ProcessingPausedError(f"Job {job_id} is paused")

    async def _load_state_for_embedding_retry(
        self,
        document_id: UUID,
        job_id: UUID,
    ) -> ProcessingState | None:
        if self._database is None:
            return None

        async with self._database.session_scope() as session:
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is None or not document.extracted_text:
                return None

            state = ProcessingState(document=document, job_id=job_id)
            state.ocr_result = OcrResult(
                text=document.extracted_text,
                page_count=document.page_count or 1,
            )
            return state

    def _infer_rate_limited_stage(
        self,
        state: ProcessingState,
        *,
        embeddings_only: bool,
    ) -> ProcessingStage:
        if embeddings_only or state.embedding is None and state.summary_output is not None:
            return ProcessingStage.EMBEDDINGS
        if state.classification is None:
            return ProcessingStage.CLASSIFICATION
        if state.metadata_output is None or state.summary_output is None:
            return ProcessingStage.METADATA_SUMMARY
        if state.ocr_result is None:
            return ProcessingStage.OCR
        return ProcessingStage.EMBEDDINGS

    def _calculate_retry_delay(self, retry_count: int, retry_after: float | None) -> float:
        base = retry_after or self._settings.embedding_retry_base_seconds
        scaled = base * (1.5 ** max(retry_count, 0))
        return min(scaled, self._settings.embedding_retry_max_seconds)

    async def _persist_rate_limited(
        self,
        document_id: UUID,
        job_id: UUID,
        state: ProcessingState,
        *,
        stage: ProcessingStage,
        error: RateLimitError,
        embeddings_only: bool = False,
    ) -> None:
        if self._database is None:
            return

        async with self._database.session_scope() as session:
            processing_repo = self._repo(session)
            job = await processing_repo.get_job(job_id)
            retry_count = job.retry_count if job is not None else 0

        delay = self._calculate_retry_delay(retry_count, error.retry_after_seconds)
        next_retry_at = datetime.now(UTC) + timedelta(seconds=delay)
        wait_reason = "rate_limit"
        message = (
            f"Waiting for {error.provider_label} rate limit. "
            f"Retry scheduled in {int(delay)} seconds."
        )

        if (
            stage == ProcessingStage.EMBEDDINGS
            and not embeddings_only
            and state.metadata_output is not None
            and state.summary_output is not None
            and state.classification is not None
            and state.ocr_result is not None
        ):
            await self._persist_document_result(
                document_id,
                job_id,
                state,
                embedding_vector=None,
                embedding_model_name=None,
                embedding_dimensions=None,
                document_status=DocumentStatus.COMPLETED,
                processing_status=ProcessingStage.EMBEDDINGS,
                mark_job_completed=False,
            )

        async with self._database.session_scope() as session:
            await self._repo(session).mark_job_rate_limited(
                job_id,
                stage=stage,
                next_retry_at=next_retry_at,
                wait_reason=wait_reason,
                error_message=message,
            )
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is not None and stage != ProcessingStage.EMBEDDINGS:
                document.processing_status = stage.value
            await self._repo(session).increment_retry_count(job_id)
            await session.commit()

        logger.info(
            "Document %s deferred until %s (stage=%s, delay=%.0fs)",
            document_id,
            next_retry_at.isoformat(),
            stage.value,
            delay,
        )

    async def _persist_document_result(
        self,
        document_id: UUID,
        job_id: UUID,
        state: ProcessingState,
        *,
        embedding_vector: list[float] | None,
        embedding_model_name: str | None,
        embedding_dimensions: int | None,
        document_status: DocumentStatus,
        processing_status: ProcessingStage,
        mark_job_completed: bool,
    ) -> None:
        if self._database is None:
            return

        classification = state.classification
        metadata_output = state.metadata_output
        summary_output = state.summary_output
        ocr_result = state.ocr_result

        if (
            classification is None
            or metadata_output is None
            or summary_output is None
            or ocr_result is None
        ):
            raise ValueError("Processing state is incomplete")

        metadata = metadata_output.metadata
        summary = summary_output.summary
        timeline_payload = [
            {
                "event_date": draft.event_date,
                "event_type": draft.event_type.value,
                "title": draft.title,
                "description": draft.description,
                "source_field": draft.source_field,
            }
            for draft in state.timeline_events
        ]

        async with self._database.session_scope() as session:
            await DocumentRepository(session).set_processing_result(
                document_id,
                extracted_text=ocr_result.text,
                page_count=ocr_result.page_count,
                document_type=classification.category,
                confidence=classification.confidence,
                reasoning=classification.reasoning,
                model_name=classification.model_name,
                patient_name=metadata.patient_name,
                doctor_name=metadata.doctor_name,
                hospital_name=metadata.hospital_name,
                document_date=metadata.document_date,
                specialization=metadata.specialization,
                diagnosis=metadata.diagnosis,
                clinical_summary=metadata.summary,
                admission_date=metadata.admission_date,
                discharge_date=metadata.discharge_date,
                follow_up=metadata.follow_up,
                medicines=[item.model_dump() for item in metadata.medicines],
                lab_measurements=[item.model_dump() for item in metadata.lab_measurements],
                procedures=metadata.procedures,
                allergies=metadata.allergies,
                medical_devices=metadata.medical_devices,
                vaccinations=metadata.vaccinations,
                metadata_model_name=metadata_output.model_name,
                short_summary=summary.short_summary,
                key_findings=summary.key_findings,
                important_dates=[
                    {"date": item.date.isoformat(), "label": item.label}
                    for item in summary.important_dates
                ],
                highlights=summary.highlights,
                summary_model_name=summary_output.model_name,
                timeline_events=timeline_payload,
                embedding_vector=embedding_vector,
                embedding_model_name=embedding_model_name,
                embedding_dimensions=embedding_dimensions,
                status=document_status,
            )
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is not None:
                document.processing_status = processing_status.value
                if mark_job_completed:
                    document.processed_at = datetime.now(UTC)

            if mark_job_completed:
                await self._repo(session).mark_job_completed(job_id)
            await session.commit()

    async def _persist_success(
        self,
        document_id: UUID,
        job_id: UUID,
        state: ProcessingState,
        *,
        embeddings_only: bool = False,
    ) -> None:
        embedding = state.embedding
        if embedding is None:
            raise ValueError("Processing state is incomplete")

        if embeddings_only:
            await self._persist_embedding_only(document_id, job_id, state, embedding)
            return

        await self._persist_document_result(
            document_id,
            job_id,
            state,
            embedding_vector=embedding.vector,
            embedding_model_name=embedding.model_name,
            embedding_dimensions=embedding.dimensions,
            document_status=DocumentStatus.COMPLETED,
            processing_status=ProcessingStage.READY,
            mark_job_completed=True,
        )

    async def _persist_embedding_only(
        self,
        document_id: UUID,
        job_id: UUID,
        state: ProcessingState,
        embedding: DocumentEmbeddingResult,
    ) -> None:
        if self._database is None:
            return

        from app.ai.embeddings.vector import PgVectorStore

        async with self._database.session_scope() as session:
            await PgVectorStore(session).upsert(
                document_id,
                embedding=embedding.vector,
                model_name=embedding.model_name,
                dimensions=embedding.dimensions,
            )
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is not None:
                document.processing_status = ProcessingStage.READY.value
                document.processed_at = datetime.now(UTC)
            await self._repo(session).mark_job_completed(job_id)
            await session.commit()

    async def _persist_rejected(
        self,
        document_id: UUID,
        job_id: UUID,
        state: ProcessingState,
    ) -> None:
        if self._database is None or state.classification is None or state.ocr_result is None:
            return

        message = (
            "This file does not look like a medical record, so it was not indexed. "
            f"{state.classification.reasoning} Delete it to keep your vault clean."
        )

        async with self._database.session_scope() as session:
            repo = DocumentRepository(session)
            document = await repo.get_by_id(document_id)
            if document is not None:
                document.page_count = state.ocr_result.page_count
                document.extracted_text = state.ocr_result.text
                document.processing_status = ProcessingStage.READY.value
                document.processed_at = datetime.now(UTC)

            await repo.set_processing_rejected(
                document_id,
                extracted_text=state.ocr_result.text,
                confidence=state.classification.confidence,
                reasoning=state.classification.reasoning,
                model_name=state.classification.model_name,
                error_message=message,
            )
            await self._repo(session).mark_job_completed(job_id)
            await session.commit()

    async def _persist_failure(
        self,
        document_id: UUID,
        job_id: UUID,
        error_message: str,
    ) -> None:
        if self._database is None:
            return

        async with self._database.session_scope() as session:
            await DocumentRepository(session).set_processing_failed(document_id, error_message)
            document = await DocumentRepository(session).get_by_id(document_id)
            if document is not None:
                document.processing_status = ProcessingStage.FAILED.value
                document.processed_at = datetime.now(UTC)
            await self._repo(session).mark_job_failed(job_id, error_message=error_message)
            await self._repo(session).increment_retry_count(job_id)
            await session.commit()

    async def _get_owned_job(self, user: User, job_id: UUID) -> ProcessingJob:
        if self._session is None:
            raise RuntimeError("Database session is required")

        job = await self._repo(self._session).get_job(job_id)
        if job is None:
            raise ProcessingJobNotFoundError()

        document = await DocumentRepository(self._session).get_by_id_and_user_id(
            job.document_id,
            user.id,
        )
        if document is None:
            raise ProcessingJobNotFoundError()
        return job
