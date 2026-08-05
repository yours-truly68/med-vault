"""Stage-based document processing pipeline (business logic only)."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from uuid import UUID

from app.ai.classifier import ClassificationError, DocumentClassifier
from app.ai.embeddings.embeddings import (
    DocumentEmbedder,
    DocumentEmbeddingResult,
    EmbeddingError,
)
from app.ai.router import AITaskRouter, create_ai_router
from app.ai.metadata import MetadataExtractionError, MetadataExtractor
from app.ai.schemas.metadata import ExtractedDocumentMetadata
from app.ai.schemas.summary import DocumentSummary
from app.ai.summarizer import DocumentSummarizer, SummarizationError
from app.core.config.settings import Settings
from app.core.database.enums import DocumentType, ProcessingStage, is_extraction_stage
from app.extraction import ExtractionEngine, ExtractionResult
from app.modules.documents.models import Document
from app.modules.documents.storage import LocalDocumentStorage
from app.modules.processing.timeline import TimelineEventDraft, build_timeline_events

logger = logging.getLogger(__name__)

PHASE1_PROCESSING_STAGES: tuple[ProcessingStage, ...] = (
    ProcessingStage.EXTRACT,
    ProcessingStage.CLASSIFICATION,
    ProcessingStage.METADATA_SUMMARY,
)

PHASE2_INDEXING_STAGES: tuple[ProcessingStage, ...] = (
    ProcessingStage.EMBEDDINGS,
)

PIPELINE_STAGES: tuple[ProcessingStage, ...] = PHASE1_PROCESSING_STAGES + PHASE2_INDEXING_STAGES


@dataclass
class ClassificationOutput:
    category: DocumentType
    confidence: float
    reasoning: str
    model_name: str


@dataclass
class MetadataOutput:
    metadata: ExtractedDocumentMetadata
    model_name: str


@dataclass
class SummaryOutput:
    summary: DocumentSummary
    model_name: str


@dataclass
class ProcessingState:
    document: Document
    job_id: UUID
    extraction_result: ExtractionResult | None = None
    classification: ClassificationOutput | None = None
    metadata_output: MetadataOutput | None = None
    summary_output: SummaryOutput | None = None
    embedding: DocumentEmbeddingResult | None = None
    timeline_events: list[TimelineEventDraft] = field(default_factory=list)
    rejected: bool = False
    stage_timings: dict[str, float] = field(default_factory=dict)


class ProcessingPipeline:
    """Runs AI stages. No database access — persistence is handled by the service."""

    def __init__(
        self,
        settings: Settings,
        *,
        extraction_engine: ExtractionEngine | None = None,
        storage: LocalDocumentStorage | None = None,
        classifier: DocumentClassifier | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        summarizer: DocumentSummarizer | None = None,
        embedder: DocumentEmbedder | None = None,
        router: AITaskRouter | None = None,
    ) -> None:
        self._settings = settings
        self._extraction = extraction_engine or ExtractionEngine(settings)
        self._storage = storage or LocalDocumentStorage(settings)

        ai_router = router or create_ai_router(settings)

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
            self._classifier = classifier or DocumentClassifier(ai_router)
            self._metadata = metadata_extractor or MetadataExtractor(ai_router)
            self._summarizer = summarizer or DocumentSummarizer(ai_router)
            self._embedder = embedder or DocumentEmbedder(ai_router)

    async def run_stage(self, stage: ProcessingStage, state: ProcessingState) -> ProcessingState:
        started = asyncio.get_event_loop().time()
        try:
            if is_extraction_stage(stage):
                result_state = await self._run_extract(state)
            elif stage == ProcessingStage.CLASSIFICATION:
                result_state = await self._run_classification(state)
            elif stage in {
                ProcessingStage.METADATA,
                ProcessingStage.SUMMARY,
                ProcessingStage.METADATA_SUMMARY,
            }:
                result_state = await self._run_metadata_and_summary(state)
            elif stage == ProcessingStage.EMBEDDINGS:
                result_state = await self._run_embeddings(state)
            else:
                raise ValueError(f"Unsupported pipeline stage: {stage}")
            
            elapsed_ms = round((asyncio.get_event_loop().time() - started) * 1000, 2)
            result_state.stage_timings[stage.value] = elapsed_ms
            logger.info("Stage %s completed for doc %s in %.2fms", stage.value, state.document.id, elapsed_ms)
            return result_state
        except Exception:
            elapsed_ms = round((asyncio.get_event_loop().time() - started) * 1000, 2)
            state.stage_timings[f"{stage.value}_error"] = elapsed_ms
            raise

    async def _run_extract(self, state: ProcessingState) -> ProcessingState:
        file_path = self._storage.resolve_path(state.document.storage_path)
        result = await self._extraction.extract(
            file_path,
            declared_content_type=state.document.content_type,
            document_id=state.document.id,
        )
        if result.quality_decision.value == "accept_with_warn":
            logger.warning(
                "Extraction accepted with warning for document %s (score=%.2f, extractor=%s)",
                state.document.id,
                result.quality_score,
                result.extractor,
            )
        state.extraction_result = result
        return state

    async def _run_classification(self, state: ProcessingState) -> ProcessingState:
        if state.extraction_result is None:
            raise ClassificationError("Extraction must run before classification")

        result = await self._classifier.classify(
            state.extraction_result.text,
            filename=state.document.original_filename,
            mime_type=state.document.content_type,
            page_count=state.extraction_result.page_count,
        )
        state.classification = ClassificationOutput(
            category=result.category,
            confidence=result.confidence,
            reasoning=result.reasoning,
            model_name=result.model_name,
        )
        if result.category == DocumentType.UNRELATED:
            state.rejected = True
        return state

    async def _run_metadata_and_summary(self, state: ProcessingState) -> ProcessingState:
        if state.extraction_result is None or state.classification is None:
            raise MetadataExtractionError(
                "Classification must run before metadata and summary"
            )

        text = state.extraction_result.text
        metadata_task = self._metadata.extract(
            text,
            document_type=state.classification.category,
        )
        summary_task = self._summarizer.summarize(
            text,
            document_type=state.classification.category,
        )
        metadata_result, summary_result = await asyncio.gather(metadata_task, summary_task)

        state.metadata_output = MetadataOutput(
            metadata=metadata_result.metadata,
            model_name=metadata_result.model_name,
        )
        state.summary_output = SummaryOutput(
            summary=summary_result.summary,
            model_name=summary_result.model_name,
        )
        state.timeline_events = build_timeline_events(
            state.document,
            metadata_result.metadata,
            summary_result.summary,
        )
        return state

    async def _run_embeddings(self, state: ProcessingState) -> ProcessingState:
        if state.rejected:
            raise EmbeddingError("Skipping embeddings for rejected document")

        if state.extraction_result is None:
            raise EmbeddingError("Extraction must run before embeddings")

        state.embedding = await self._embedder.embed(state.extraction_result.text)
        return state
