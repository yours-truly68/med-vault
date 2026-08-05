"""Worker entry point for document processing.

Compatible with FastAPI BackgroundTasks, Celery, ARQ, and Dramatiq — only the
enqueue mechanism changes; this function stays the orchestration entry point.
"""

from __future__ import annotations

from uuid import UUID

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.modules.processing.service import ProcessingService


async def process_document(
    document_id: UUID,
    *,
    database: Database,
    settings: Settings,
) -> None:
    service = ProcessingService(session=None, settings=settings, database=database)
    await service.process_document(document_id)
