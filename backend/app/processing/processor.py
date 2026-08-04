"""Document processing: OCR → classify → metadata → summarize → embed → persist."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.ai.classifier import ClassificationError, DocumentClassifier
from app.ai.embeddings.embeddings import (
    DocumentEmbedder,
    DocumentEmbeddingResult,
    EmbeddingError,
)
from app.ai.embeddings.factory import create_embedding_provider
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.llm.factory import create_llm_provider
from app.ai.llm.provider import LLMProvider
from app.ai.metadata import MetadataExtractionError, MetadataExtractor
from app.ai.ocr import OcrError, OcrService
from app.ai.schemas.metadata import ExtractedDocumentMetadata
from app.ai.schemas.summary import DocumentSummary
from app.ai.summarizer import DocumentSummarizer, SummarizationError
from app.core.config.settings import Settings
from app.core.database.enums import DocumentStatus, DocumentType
from app.core.database.session import Database
from app.modules.documents.models import Document
from app.modules.documents.repository import DocumentRepository
from app.modules.documents.storage import LocalDocumentStorage

logger = logging.getLogger(__name__)

PROCESSABLE_STATUSES = frozenset({
    DocumentStatus.PENDING.value,
    DocumentStatus.PROCESSING.value,
})


class DocumentProcessor:
    def __init__(
        self,
        database: Database,
        settings: Settings,
        *,
        ocr: OcrService | None = None,
        storage: LocalDocumentStorage | None = None,
        classifier: DocumentClassifier | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        summarizer: DocumentSummarizer | None = None,
        embedder: DocumentEmbedder | None = None,
        llm_provider: LLMProvider | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self._database = database
        self._settings = settings
        self._ocr = ocr or OcrService(settings)
        self._storage = storage or LocalDocumentStorage(settings)

        if (
            classifier is not None
            and metadata_extractor is not None
            and summarizer is not None
            and embedder is not None
        ):
            self._classifier = classifier
            self._metadata = metadata_extractor
            self._summarizer = summarizer
            self._embedder = embedder
        else:
            chat_provider = llm_provider or create_llm_provider(settings)
            self._classifier = classifier or DocumentClassifier(chat_provider)
            self._metadata = metadata_extractor or MetadataExtractor(chat_provider)
            self._summarizer = summarizer or DocumentSummarizer(chat_provider)
            self._embedder = embedder or DocumentEmbedder(
                embedding_provider or create_embedding_provider(settings)
            )

    async def process(self, document_id: UUID) -> None:
        document = await self._get_document(document_id)
        if document is None:
            logger.warning("Document %s not found; skipping processing", document_id)
            return

        if document.status not in PROCESSABLE_STATUSES:
            logger.info(
                "Document %s has status %r; skipping processing",
                document_id,
                document.status,
            )
            return

        await self._mark_processing(document_id)

        try:
            file_path = self._storage.resolve_path(document.storage_path)
            extracted_text = await asyncio.to_thread(
                self._ocr.extract_text,
                file_path,
                document.content_type,
            )
            classification = await self._classifier.classify(extracted_text)

            # Reject non-medical / unrelated content: no metadata, summary, or embeddings.
            if classification.category == DocumentType.UNRELATED:
                await self._mark_rejected(
                    document_id,
                    extracted_text=extracted_text,
                    confidence=classification.confidence,
                    reasoning=classification.reasoning,
                    model_name=classification.model_name,
                )
                logger.info(
                    "Document %s rejected as unrelated (confidence=%.2f)",
                    document_id,
                    classification.confidence,
                )
                return

            metadata_result = await self._metadata.extract(
                extracted_text,
                document_type=classification.category,
            )
            summary_result = await self._summarizer.summarize(
                extracted_text,
                document_type=classification.category,
            )
            embedding_result = await self._embedder.embed(extracted_text)
            await self._mark_completed(
                document_id,
                extracted_text=extracted_text,
                category=classification.category,
                confidence=classification.confidence,
                reasoning=classification.reasoning,
                model_name=classification.model_name,
                metadata=metadata_result.metadata,
                metadata_model_name=metadata_result.model_name,
                summary=summary_result.summary,
                summary_model_name=summary_result.model_name,
                embedding=embedding_result,
            )
            logger.info(
                "Document %s processed: type=%s confidence=%.2f dims=%s",
                document_id,
                classification.category.value,
                classification.confidence,
                embedding_result.dimensions,
            )
        except (
            OcrError,
            ClassificationError,
            MetadataExtractionError,
            SummarizationError,
            EmbeddingError,
            FileNotFoundError,
            ValueError,
            Exception,
        ) as exc:
            logger.exception("Document %s processing failed", document_id)
            await self._mark_failed(document_id, str(exc))

    async def reprocess(self, document_id: UUID) -> None:
        """Reset a document to pending and run the full processing pipeline."""
        document = await self._get_document(document_id)
        if document is None:
            logger.warning("Document %s not found; skipping reprocess", document_id)
            return

        async with self._database.session_scope() as session:
            await DocumentRepository(session).reset_for_reprocessing(document_id)

        await self.process(document_id)

    async def _get_document(self, document_id: UUID) -> Document | None:
        async with self._database.session_scope() as session:
            return await DocumentRepository(session).get_by_id(document_id)

    async def _mark_processing(self, document_id: UUID) -> None:
        async with self._database.session_scope() as session:
            await DocumentRepository(session).update_status(
                document_id,
                DocumentStatus.PROCESSING,
            )

    async def _mark_completed(
        self,
        document_id: UUID,
        *,
        extracted_text: str,
        category: DocumentType,
        confidence: float,
        reasoning: str,
        model_name: str,
        metadata: ExtractedDocumentMetadata,
        metadata_model_name: str,
        summary: DocumentSummary,
        summary_model_name: str,
        embedding: DocumentEmbeddingResult,
    ) -> None:
        async with self._database.session_scope() as session:
            await DocumentRepository(session).set_processing_result(
                document_id,
                extracted_text=extracted_text,
                document_type=category,
                confidence=confidence,
                reasoning=reasoning,
                model_name=model_name,
                patient_name=metadata.patient_name,
                doctor_name=metadata.doctor_name,
                hospital_name=metadata.hospital_name,
                document_date=metadata.document_date,
                specialization=metadata.specialization,
                diagnosis=metadata.diagnosis,
                medicines=[item.model_dump() for item in metadata.medicines],
                metadata_model_name=metadata_model_name,
                short_summary=summary.short_summary,
                key_findings=summary.key_findings,
                important_dates=[
                    {"date": item.date.isoformat(), "label": item.label}
                    for item in summary.important_dates
                ],
                summary_model_name=summary_model_name,
                embedding_vector=embedding.vector,
                embedding_model_name=embedding.model_name,
                embedding_dimensions=embedding.dimensions,
                status=DocumentStatus.COMPLETED,
            )

    async def _mark_failed(self, document_id: UUID, error_message: str) -> None:
        async with self._database.session_scope() as session:
            await DocumentRepository(session).set_processing_failed(
                document_id,
                error_message,
            )

    async def _mark_rejected(
        self,
        document_id: UUID,
        *,
        extracted_text: str,
        confidence: float,
        reasoning: str,
        model_name: str,
    ) -> None:
        message = (
            "This file does not look like a medical record, so it was not indexed. "
            f"{reasoning} Delete it to keep your vault clean."
        )
        async with self._database.session_scope() as session:
            await DocumentRepository(session).set_processing_rejected(
                document_id,
                extracted_text=extracted_text,
                confidence=confidence,
                reasoning=reasoning,
                model_name=model_name,
                error_message=message,
            )
