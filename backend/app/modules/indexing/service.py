"""Indexing service: handles chunking, embedding generation, and vector storage."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from app.ai.embeddings import DocumentEmbedder, PgVectorStore
from app.ai.router import create_ai_router
from app.core.config.settings import Settings
from app.core.database.enums import DocumentStatus, IndexingStatus
from app.core.database.session import Database
from app.modules.documents.repository import DocumentRepository

if TYPE_CHECKING:
    from app.modules.processing.instrumentation import PipelineContext

logger = logging.getLogger(__name__)


class IndexingService:
    """Orchestrates Phase 2 document indexing (embeddings & vector persistence)."""

    def __init__(
        self,
        settings: Settings,
        *,
        database: Database | None = None,
        embedder: DocumentEmbedder | None = None,
    ) -> None:
        self._settings = settings
        self._database = database
        if embedder is not None:
            self._embedder = embedder
        else:
            router = create_ai_router(settings)
            self._embedder = DocumentEmbedder(router)

    async def index_document(
        self,
        document_id: UUID,
        *,
        pipeline_ctx: PipelineContext | None = None,
    ) -> None:
        """Execute Phase 2 background indexing for a document."""
        from app.modules.processing.instrumentation import (
            PipelineContext as _PipelineContext,
            instrument_stage,
            log_stage_enter,
            log_stage_exit,
        )

        ctx = pipeline_ctx or _PipelineContext(
            document_id=document_id,
            worker_name="IndexingService",
        )

        if self._database is None:
            logger.error("Database handle is required for document indexing")
            return

        # ── Stage: load_document_for_indexing ──
        async with instrument_stage(ctx, "load_document_for_indexing") as meta:
            async with self._database.session_scope() as session:
                doc_repo = DocumentRepository(session)
                document = await doc_repo.get_by_id(document_id)
                if document is None or not document.extracted_text:
                    logger.warning("Document %s has no text to index; skipping indexing", document_id)
                    meta["result"] = "skipped_no_text"
                    return

                meta["text_length"] = len(document.extracted_text)
                document.indexing_status = IndexingStatus.INDEXING.value
                document.indexing_error = None
                await session.commit()

        try:
            # ── Stage: embedding_generation ──
            async with instrument_stage(ctx, "embedding_generation") as meta:
                logger.info("Starting embedding generation for doc %s", document_id)
                embedding_result = await self._embedder.embed(document.extracted_text)
                meta["dimensions"] = embedding_result.dimensions
                meta["model"] = embedding_result.model_name
                meta["vector_length"] = len(embedding_result.vector)

            # ── Stage: pgvector_upsert ──
            async with instrument_stage(ctx, "pgvector_upsert") as meta:
                async with self._database.session_scope() as session:
                    logger.info(
                        "Upserting vector embedding into pgvector for doc %s (dim=%d, model=%s)",
                        document_id,
                        embedding_result.dimensions,
                        embedding_result.model_name,
                    )
                    vector_store = PgVectorStore(session)
                    await vector_store.upsert(
                        document_id,
                        embedding=embedding_result.vector,
                        model_name=embedding_result.model_name,
                        dimensions=embedding_result.dimensions,
                    )
                    meta["model"] = embedding_result.model_name
                    meta["dimensions"] = embedding_result.dimensions
                    await session.commit()

            # ── Stage: mark_indexed ──
            async with instrument_stage(ctx, "mark_indexed"):
                async with self._database.session_scope() as session:
                    doc_repo = DocumentRepository(session)
                    doc = await doc_repo.get_by_id(document_id)
                    if doc is not None:
                        doc.indexing_status = IndexingStatus.INDEXED.value
                        doc.status = DocumentStatus.INDEXED.value
                    await session.commit()

            logger.info("Document %s successfully indexed into pgvector", document_id)
        except Exception as exc:
            logger.exception("Background indexing failed for document %s", document_id)
            async with self._database.session_scope() as session:
                doc_repo = DocumentRepository(session)
                doc = await doc_repo.get_by_id(document_id)
                if doc is not None:
                    doc.indexing_status = IndexingStatus.FAILED.value
                    doc.indexing_error = str(exc)[:4000]
                await session.commit()

