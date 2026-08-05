"""Worker entry point for document processing (Phase 1)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.modules.processing.service import ProcessingService
from app.queue.interface import IJobQueue

if TYPE_CHECKING:
    from app.modules.processing.instrumentation import PipelineContext


async def process_document(
    document_id: UUID,
    *,
    database: Database,
    settings: Settings,
    job_queue: IJobQueue | None = None,
    pipeline_ctx: PipelineContext | None = None,
) -> None:
    """Worker entry point that runs Phase 1 processing for a document."""
    service = ProcessingService(
        session=None,
        settings=settings,
        database=database,
        job_queue=job_queue,
    )
    await service.process_document(document_id, pipeline_ctx=pipeline_ctx)
