from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.database.enums import ProcessingJobStatus, ProcessingStage


class ProcessingJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    stage: ProcessingStage
    status: ProcessingJobStatus
    started_at: datetime | None
    completed_at: datetime | None
    paused_at: datetime | None
    error_message: str | None
    retry_count: int
    next_retry_at: datetime | None = None
    wait_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ProcessingStatusResponse(BaseModel):
    globally_paused: bool
    active_jobs: int
    paused_jobs: int
    pending_jobs: int
    rate_limited_jobs: int = 0


class ProcessingControlResponse(BaseModel):
    globally_paused: bool
    message: str
