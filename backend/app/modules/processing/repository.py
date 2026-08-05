from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.enums import ProcessingJobStatus, ProcessingStage
from app.modules.processing.models import ProcessingControl, ProcessingJob


class ProcessingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_job(self, document_id: UUID) -> ProcessingJob:
        job = ProcessingJob(
            document_id=document_id,
            stage=ProcessingStage.UPLOADED.value,
            status=ProcessingJobStatus.PENDING.value,
        )
        self._session.add(job)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def get_job(self, job_id: UUID) -> ProcessingJob | None:
        result = await self._session.execute(
            select(ProcessingJob).where(ProcessingJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_job_for_document(self, document_id: UUID) -> ProcessingJob | None:
        result = await self._session.execute(
            select(ProcessingJob)
            .where(ProcessingJob.document_id == document_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_job_running(self, job_id: UUID, *, stage: ProcessingStage) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status=ProcessingJobStatus.RUNNING.value,
                stage=stage.value,
                started_at=now,
                paused_at=None,
                error_message=None,
            )
        )

    async def advance_job_stage(self, job_id: UUID, *, stage: ProcessingStage) -> None:
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(stage=stage.value)
        )

    async def mark_job_paused(self, job_id: UUID) -> None:
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status=ProcessingJobStatus.PAUSED.value,
                paused_at=datetime.now(UTC),
            )
        )

    async def mark_job_completed(self, job_id: UUID) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status=ProcessingJobStatus.COMPLETED.value,
                stage=ProcessingStage.READY.value,
                completed_at=now,
                paused_at=None,
                error_message=None,
            )
        )

    async def mark_job_failed(self, job_id: UUID, *, error_message: str) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status=ProcessingJobStatus.FAILED.value,
                stage=ProcessingStage.FAILED.value,
                completed_at=now,
                error_message=error_message,
                next_retry_at=None,
                wait_reason=None,
            )
        )

    async def mark_job_rate_limited(
        self,
        job_id: UUID,
        *,
        stage: ProcessingStage,
        next_retry_at: datetime,
        wait_reason: str,
        error_message: str | None = None,
    ) -> None:
        await self._session.execute(
            update(ProcessingJob)
            .where(ProcessingJob.id == job_id)
            .values(
                status=ProcessingJobStatus.RATE_LIMITED.value,
                stage=stage.value,
                error_message=error_message,
                next_retry_at=next_retry_at,
                wait_reason=wait_reason,
            )
        )

    async def list_jobs_ready_for_retry(self, *, limit: int = 20) -> list[ProcessingJob]:
        now = datetime.now(UTC)
        result = await self._session.execute(
            select(ProcessingJob)
            .where(
                ProcessingJob.status == ProcessingJobStatus.RATE_LIMITED.value,
                ProcessingJob.next_retry_at.is_not(None),
                ProcessingJob.next_retry_at <= now,
            )
            .order_by(ProcessingJob.next_retry_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def requeue_job_for_retry(self, job_id: UUID) -> ProcessingJob | None:
        job = await self.get_job(job_id)
        if job is None:
            return None

        job.status = ProcessingJobStatus.PENDING.value
        job.next_retry_at = None
        job.wait_reason = None
        job.error_message = None
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def increment_retry_count(self, job_id: UUID) -> None:
        job = await self.get_job(job_id)
        if job is None:
            return
        job.retry_count += 1
        await self._session.flush()

    async def resume_job(self, job_id: UUID) -> ProcessingJob | None:
        job = await self.get_job(job_id)
        if job is None:
            return None
        if job.status != ProcessingJobStatus.PAUSED.value:
            return job

        job.status = ProcessingJobStatus.PENDING.value
        job.paused_at = None
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def pause_job(self, job_id: UUID) -> ProcessingJob | None:
        job = await self.get_job(job_id)
        if job is None:
            return None
        if job.status in {
            ProcessingJobStatus.COMPLETED.value,
            ProcessingJobStatus.FAILED.value,
        }:
            return job

        job.status = ProcessingJobStatus.PAUSED.value
        job.paused_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(job)
        return job

    async def count_rate_limited_jobs(self) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(ProcessingJob)
            .where(ProcessingJob.status == ProcessingJobStatus.RATE_LIMITED.value)
        )
        return int(result.scalar_one())

    async def get_or_create_control(self) -> ProcessingControl:
        result = await self._session.execute(select(ProcessingControl).limit(1))
        control = result.scalar_one_or_none()
        if control is not None:
            return control

        control = ProcessingControl(globally_paused=False, updated_at=datetime.now(UTC))
        self._session.add(control)
        await self._session.flush()
        await self._session.refresh(control)
        return control

    async def is_globally_paused(self) -> bool:
        control = await self.get_or_create_control()
        return bool(control.globally_paused)

    async def set_global_pause(self, paused: bool) -> ProcessingControl:
        control = await self.get_or_create_control()
        control.globally_paused = paused
        control.updated_at = datetime.now(UTC)
        await self._session.flush()
        await self._session.refresh(control)
        return control

    async def count_jobs_by_status(self) -> dict[str, int]:
        result = await self._session.execute(
            select(ProcessingJob.status, func.count())
            .group_by(ProcessingJob.status)
        )
        return {status: count for status, count in result.all()}
