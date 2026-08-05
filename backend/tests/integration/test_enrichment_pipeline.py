"""End-to-end integration tests for document processing and enrichment pipeline."""

from __future__ import annotations

from pathlib import Path
import pytest

import app.core.database.models  # Register SQLAlchemy models
from app.core.config.settings import Settings
from app.core.database.enums import DocumentType, ProcessingStage
from app.extraction import ExtractionEngine
from app.modules.documents.models import Document
from app.modules.processing.pipeline import ProcessingPipeline, ProcessingState, PIPELINE_STAGES
from uuid import uuid4

TEST_DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "test-documents"


@pytest.mark.asyncio
async def test_real_pdf_processing_pipeline_resilience():
    """Upload and process a real PDF from test-documents/ through extraction, classification, metadata, and summary."""
    pdf_path = TEST_DOCS_DIR / "John_Doe_Blood_Report_1.pdf"
    if not pdf_path.exists():
        pytest.skip(f"Test document missing: {pdf_path}")

    settings = Settings(
        openai_api_key="mock",
        ocr_max_workers=2,
        tesseract_enabled=False,
        ocr_pdf_dpi=300,
    )
    pipeline = ProcessingPipeline(settings)

    doc = Document(
        id=uuid4(),
        original_filename=pdf_path.name,
        storage_path=str(pdf_path),
        content_type="application/pdf",
    )
    state = ProcessingState(document=doc, job_id=uuid4())

    # Step 1: Extraction
    state = await pipeline.run_stage(ProcessingStage.EXTRACT, state)
    assert state.extraction_result is not None
    assert state.extraction_result.character_count > 50

    # Step 2: Classification (Mocked to avoid network LLM requirement in integration unit runner)
    from app.modules.processing.pipeline import ClassificationOutput
    state.classification = ClassificationOutput(
        category=DocumentType.LAB_REPORT,
        confidence=0.98,
        reasoning="Medical lab panel report",
        model_name="test-classifier",
    )

    # Step 3: Metadata & Summary (Decoupled execution test)
    state = await pipeline.run_stage(ProcessingStage.METADATA_SUMMARY, state)

    assert state.metadata_output is not None
    assert state.metadata_output.metadata is not None
    # Verify that pipeline state completed without raising an exception
    assert state.timeline_events is not None
