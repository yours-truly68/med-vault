"""Backward-compatible wrapper around ProcessingService."""

from __future__ import annotations

from uuid import UUID

from app.core.config.settings import Settings
from app.core.database.session import Database
from app.modules.processing.service import ProcessingService


class DocumentProcessor:
    """Deprecated: use ProcessingService and process_document worker entry point."""

    def __init__(self, database: Database, settings: Settings) -> None:
        self._database = database
        self._settings = settings
        self._service = ProcessingService(
            session=None,
            settings=settings,
            database=database,
        )

    async def process(self, document_id: UUID) -> None:
        await self._service.process_document(document_id)

    async def reprocess(self, document_id: UUID) -> None:
        await self._service.reprocess_document(document_id)
