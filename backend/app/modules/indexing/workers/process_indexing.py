"""Worker entry point for document indexing (Phase 2)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.modules.indexing.service import IndexingService

if TYPE_CHECKING:
    from app.modules.processing.instrumentation import PipelineContext


async def process_indexing(
    document_id: UUID,
    *,
    database: Database,
    settings: Settings,
    pipeline_ctx: PipelineContext | None = None,
) -> None:
    """Worker entry point that runs Phase 2 indexing for a document."""
    service = IndexingService(settings=settings, database=database)
    await service.index_document(document_id, pipeline_ctx=pipeline_ctx)
