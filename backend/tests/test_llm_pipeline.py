"""Live LLM pipeline tests: extract → classify → summarize.

Run explicitly (uses your gateway key and incurs cost/rate limits):

    RUN_LLM_TESTS=1 uv run pytest -m llm -q

What these protect
------------------
- Real credentials resolve and the chat provider responds.
- A medical fixture can be classified and summarized.
- A non-medical decoy is not confidently treated as a prescription.
- Rate limits are reported as skips (not red failures) when the provider throttles.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.ai.classifier import ClassificationError, DocumentClassifier
from app.ai.errors import RateLimitError
from app.ai.router import create_ai_router
from app.ai.summarizer import DocumentSummarizer, SummarizationError
from app.core.config.settings import Settings
from app.core.database.enums import DocumentType
from app.extraction import ExtractionEngine

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def _resolve_fixture(name: str, test_documents_dir: Path, dummy_dataset_dir: Path) -> Path:
    for root in (test_documents_dir, dummy_dataset_dir):
        path = root / name
        if path.is_file():
            return path
    raise FileNotFoundError(name)


def _skip_on_rate_limit(exc: Exception) -> None:
    if isinstance(exc, RateLimitError):
        pytest.skip(f"LLM provider rate-limited: {exc}")
    message = str(exc).lower()
    if "429" in message or "rate limit" in message:
        pytest.skip(f"LLM provider rate-limited: {exc}")


@pytest.mark.llm
@pytest.mark.asyncio
async def test_llm_provider_resolves(llm_settings: Settings) -> None:
    router = create_ai_router(llm_settings)
    assert router is not None
    assert bool(llm_settings.openai_api_key or llm_settings.llm_api_key)


@pytest.mark.llm
@pytest.mark.asyncio
async def test_extract_classify_summarize_medical_fixture(
    llm_settings: Settings,
    test_documents_dir: Path,
    dummy_dataset_dir: Path,
) -> None:
    """One medical PDF: extract → classify → summarize (2 LLM calls)."""
    path = _resolve_fixture(
        "John_Doe_Blood_Report_1.pdf",
        test_documents_dir,
        dummy_dataset_dir,
    )
    engine = ExtractionEngine(llm_settings)
    router = create_ai_router(llm_settings)
    classifier = DocumentClassifier(router)
    summarizer = DocumentSummarizer(router)

    extraction = await engine.extract(path, declared_content_type="application/pdf")
    assert extraction.character_count > 50
    assert "Patient" in extraction.text or "patient" in extraction.text.lower()

    try:
        classification = await classifier.classify(
            extraction.text,
            filename=path.name,
            mime_type="application/pdf",
            page_count=extraction.page_count,
        )
        summary = await summarizer.summarize(
            extraction.text,
            document_type=classification.category,
        )
    except (ClassificationError, SummarizationError, RateLimitError) as exc:
        _skip_on_rate_limit(exc)
        raise

    assert classification.category != DocumentType.UNRELATED
    assert classification.category in {
        DocumentType.LAB_REPORT,
        DocumentType.OTHER,
        DocumentType.DISCHARGE_SUMMARY,
        DocumentType.IMAGING_REPORT,
    }
    assert summary.summary.short_summary.strip()
    assert len(summary.summary.short_summary.strip()) >= 20

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {
        "filename": path.name,
        "extractor": extraction.extractor,
        "quality_score": round(extraction.quality_score, 4),
        "category": classification.category.value,
        "classification_confidence": classification.confidence,
        "classification_reasoning": classification.reasoning,
        "summary": summary.summary.short_summary,
        "key_findings": summary.summary.key_findings[:5],
        "model": classification.model_name,
    }
    (OUTPUT_DIR / "llm_pipeline_medical_summary.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )


@pytest.mark.llm
@pytest.mark.asyncio
async def test_classify_non_medical_decoy(
    llm_settings: Settings,
    test_documents_dir: Path,
    dummy_dataset_dir: Path,
) -> None:
    """One decoy PDF: extract → classify (1 LLM call)."""
    path = _resolve_fixture("Bank_Statement.pdf", test_documents_dir, dummy_dataset_dir)
    engine = ExtractionEngine(llm_settings)
    classifier = DocumentClassifier(create_ai_router(llm_settings))

    extraction = await engine.extract(path, declared_content_type="application/pdf")
    try:
        classification = await classifier.classify(
            extraction.text,
            filename=path.name,
            mime_type="application/pdf",
            page_count=extraction.page_count,
        )
    except (ClassificationError, RateLimitError) as exc:
        _skip_on_rate_limit(exc)
        raise

    # Decoys in this dataset are styled like medical forms; never allow a
    # high-confidence prescription mislabel.
    if classification.category == DocumentType.PRESCRIPTION:
        assert classification.confidence < 0.7

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "llm_pipeline_non_medical_summary.json").write_text(
        json.dumps(
            {
                "filename": path.name,
                "category": classification.category.value,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
