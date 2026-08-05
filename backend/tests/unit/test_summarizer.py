"""Unit and regression tests for DocumentSummarizer, DocumentSummary highlights coercion, and decoupled processing pipeline."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
import pytest

import app.core.database.models  # Ensure all SQLAlchemy models are registered
from app.ai.providers.base import GenerationResult, TokenUsage
from app.ai.summarizer import DocumentSummarizer, SummarizationError
from app.ai.schemas.summary import DocumentSummary
from app.core.config.settings import Settings
from app.core.database.enums import DocumentType
from app.modules.processing.pipeline import (
    ClassificationOutput,
    ProcessingPipeline,
    ProcessingState,
    ProcessingStage,
)
from app.extraction import ExtractionResult, QualityDecision
from app.ai.schemas.metadata import ExtractedDocumentMetadata
from app.modules.documents.models import Document
from app.modules.documents.schemas import DocumentSummaryResponse


def test_highlights_coercion_prevents_object_stringification():
    """Verify DocumentSummary and DocumentSummaryResponse unwrap dict objects and stringified JSON into clean text."""
    payload_with_objects = {
        "short_summary": "Patient John Doe underwent complete blood panel.",
        "key_findings": ["Hemoglobin 14.2 g/dL"],
        "important_dates": [],
        "highlights": [
            {"item": "Patient: Mr. Khadar Basha K.S."},
            {"highlight": "Age: 81 Years / Male"},
            '{"item": "Referring Hospital: K.M.C. Manipal"}',
            "{'item': 'Laboratory: Hegde Laboratory'}",
            "Test Performed: Complete Blood Count",
        ],
    }

    summary = DocumentSummary.model_validate(payload_with_objects)
    assert len(summary.highlights) == 5
    assert summary.highlights[0] == "Patient: Mr. Khadar Basha K.S."
    assert summary.highlights[1] == "Age: 81 Years / Male"
    assert summary.highlights[2] == "Referring Hospital: K.M.C. Manipal"
    assert summary.highlights[3] == "Laboratory: Hegde Laboratory"
    assert summary.highlights[4] == "Test Performed: Complete Blood Count"

    # Verify API Response schema unwrap as well
    api_response = DocumentSummaryResponse.model_validate(payload_with_objects)
    assert api_response.highlights == [
        "Patient: Mr. Khadar Basha K.S.",
        "Age: 81 Years / Male",
        "Referring Hospital: K.M.C. Manipal",
        "Laboratory: Hegde Laboratory",
        "Test Performed: Complete Blood Count",
    ]


@pytest.mark.asyncio
async def test_summarize_success():
    mock_router = MagicMock()
    valid_json = (
        '{\n'
        '  "short_summary": "Patient John Doe underwent routine blood panel testing.",\n'
        '  "key_findings": ["Hemoglobin 14.2 g/dL"],\n'
        '  "important_dates": [{"date": "2026-01-15", "label": "Report Date"}],\n'
        '  "highlights": ["Normal CBC"]\n'
        '}'
    )
    mock_router.structured_output = AsyncMock(
        return_value=GenerationResult(
            content=valid_json,
            model="test-model",
            provider="test-provider",
            usage=TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            finish_reason="stop",
        )
    )

    summarizer = DocumentSummarizer(mock_router)
    result = await summarizer.summarize("Sample medical text", document_type=DocumentType.LAB_REPORT)

    assert result.model_name == "test-model"
    assert "John Doe" in result.summary.short_summary
    assert len(result.summary.key_findings) == 1
    assert mock_router.structured_output.call_count == 1


@pytest.mark.asyncio
async def test_summarize_invalid_json_triggers_retry_success():
    mock_router = MagicMock()
    truncated_json = '{"short_summary": "Patient John Doe underwent routine blood testing'
    valid_json = (
        '{\n'
        '  "short_summary": "Patient John Doe underwent routine blood panel testing.",\n'
        '  "key_findings": ["Hemoglobin 14.2 g/dL"],\n'
        '  "important_dates": [],\n'
        '  "highlights": []\n'
        '}'
    )

    # First call returns truncated JSON, second call returns valid JSON
    mock_router.structured_output = AsyncMock(
        side_effect=[
            GenerationResult(content=truncated_json, model="test-model", provider="test-provider", finish_reason="length"),
            GenerationResult(content=valid_json, model="test-model", provider="test-provider", finish_reason="stop"),
        ]
    )

    summarizer = DocumentSummarizer(mock_router)
    result = await summarizer.summarize("Sample medical text", document_type=DocumentType.LAB_REPORT)

    assert result.summary.short_summary.startswith("Patient John Doe")
    assert mock_router.structured_output.call_count == 2


@pytest.mark.asyncio
async def test_summarize_invalid_json_retry_fails():
    mock_router = MagicMock()
    truncated_json = '{"short_summary": "Truncated...'

    mock_router.structured_output = AsyncMock(
        return_value=GenerationResult(
            content=truncated_json, model="test-model", provider="test-provider", finish_reason="length"
        )
    )

    summarizer = DocumentSummarizer(mock_router)
    with pytest.raises(SummarizationError) as exc_info:
        await summarizer.summarize("Sample medical text", document_type=DocumentType.LAB_REPORT)

    assert "Summary failed structured parsing after retry" in str(exc_info.value)
    assert mock_router.structured_output.call_count == 2


@pytest.mark.asyncio
async def test_summarize_pydantic_validation_failure_triggers_retry():
    mock_router = MagicMock()
    # Missing required short_summary field
    invalid_schema = '{"key_findings": ["Test"]}'
    valid_json = (
        '{\n'
        '  "short_summary": "Valid summary text.",\n'
        '  "key_findings": ["Test"],\n'
        '  "important_dates": [],\n'
        '  "highlights": []\n'
        '}'
    )

    mock_router.structured_output = AsyncMock(
        side_effect=[
            GenerationResult(content=invalid_schema, model="test-model", provider="test-provider"),
            GenerationResult(content=valid_json, model="test-model", provider="test-provider"),
        ]
    )

    summarizer = DocumentSummarizer(mock_router)
    result = await summarizer.summarize("Sample medical text", document_type=DocumentType.LAB_REPORT)

    assert result.summary.short_summary == "Valid summary text."
    assert mock_router.structured_output.call_count == 2


@pytest.mark.asyncio
async def test_pipeline_summary_failure_does_not_fail_metadata_or_pipeline():
    """Verify that when summary generation fails, metadata is preserved and summary_output becomes None without crashing."""
    settings = Settings(
        openai_api_key="mock",
        ocr_max_workers=2,
        tesseract_enabled=False,
        ocr_pdf_dpi=300,
    )
    pipeline = ProcessingPipeline(settings)

    # Mock metadata extractor to succeed
    mock_meta_result = MagicMock()
    mock_meta_result.model_name = "meta-model"
    mock_meta_result.metadata = ExtractedDocumentMetadata(
        patient_name="John Doe",
        doctor_name="Dr. Smith",
        summary="Clinical summary from metadata",
    )
    pipeline._metadata.extract = AsyncMock(return_value=mock_meta_result)

    # Mock summarizer to raise SummarizationError
    pipeline._summarizer.summarize = AsyncMock(
        side_effect=SummarizationError("Summary JSON parsing failed")
    )

    # Build processing state with extraction and classification done
    doc = Document(id=uuid4(), original_filename="test.pdf", storage_path="path/test.pdf")
    state = ProcessingState(
        document=doc,
        job_id=uuid4(),
        extraction_result=ExtractionResult(
            text="Document text here",
            character_count=100,
            page_count=1,
            extractor="pymupdf",
            confidence=1.0,
            quality_score=0.9,
            quality_decision=QualityDecision.ACCEPT,
            elapsed_ms=50,
        ),
        classification=ClassificationOutput(
            category=DocumentType.LAB_REPORT,
            confidence=0.95,
            reasoning="Lab report format",
            model_name="class-model",
        ),
    )

    # Execute metadata and summary stage
    updated_state = await pipeline.run_stage(ProcessingStage.METADATA_SUMMARY, state)

    # Metadata must be present, summary_output must be None, pipeline does NOT raise exception
    assert updated_state.metadata_output is not None
    assert updated_state.metadata_output.metadata.patient_name == "John Doe"
    assert updated_state.summary_output is None
    assert updated_state.timeline_events is not None
