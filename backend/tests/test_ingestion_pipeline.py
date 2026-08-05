"""Ingestion pipeline: upload → extraction, plus dataset extraction summary.

What these tests protect
------------------------
1. Uploaded fixture PDFs are extractable by the Extraction Engine.
2. Medical dummy documents produce usable text without falling back to OCR/Vision.
3. Non-medical decoys still extract (classification is a later AI stage).
4. A dataset-wide summary report is generated so we can compare extractors/quality.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from uuid import uuid4

import pytest

from app.core.config.settings import Settings
from app.extraction import ExtractionEngine
from app.extraction.models import ExtractorName, QualityDecision
from app.modules.documents.storage import LocalDocumentStorage
from tests.conftest import make_upload_file

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass
class ExtractionSummaryRow:
    filename: str
    category: str
    extractor: str
    quality_score: float
    quality_decision: str
    confidence: float
    character_count: int
    page_count: int
    elapsed_ms: int
    cache_hit: bool
    warnings: list[str]
    text_preview: str


def _category_for(path: Path) -> str:
    name = path.name.lower()
    if any(
        token in name
        for token in (
            "bank",
            "electricity",
            "rental",
            "vehicle",
            "internet",
            "insurance",
            "invoice",
        )
    ):
        return "non_medical"
    if "blood" in name:
        return "lab_report"
    if "prescription" in name:
        return "prescription"
    if "hospital_bill" in name or "bill" in name:
        return "hospital_bill"
    if "scanning" in name or "xray" in name or "fracture" in name:
        return "imaging_report"
    if "diagnosis" in name or "oncology" in name or "diabetes" in name:
        return "diagnosis_report"
    return "medical_other"


@pytest.mark.asyncio
async def test_upload_then_extract_medical_pdf(
    extraction_settings: Settings,
    medical_fixture_pdfs: list[Path],
) -> None:
    """End-to-end storage → extract for a real blood report."""
    storage = LocalDocumentStorage(extraction_settings)
    engine = ExtractionEngine(extraction_settings)
    source = medical_fixture_pdfs[0]
    upload = make_upload_file(source)

    try:
        saved = await storage.save(
            user_id=uuid4(),
            family_member_id=uuid4(),
            upload=upload,
        )
    finally:
        await upload.close()

    path = storage.resolve_path(saved.storage_path)
    result = await engine.extract(
        path,
        declared_content_type=saved.content_type,
        document_id=uuid4(),
    )

    assert result.character_count > 50
    assert result.page_count >= 1
    assert result.extractor == ExtractorName.PYMUPDF.value
    assert result.quality_decision in {
        QualityDecision.ACCEPT,
        QualityDecision.ACCEPT_WITH_WARN,
    }
    assert result.quality_score >= extraction_settings.extraction_quality_warn_threshold
    assert "Patient" in result.text or "patient" in result.text.lower()


@pytest.mark.asyncio
async def test_extract_representative_medical_fixtures(
    extraction_settings: Settings,
    medical_fixture_pdfs: list[Path],
) -> None:
    engine = ExtractionEngine(extraction_settings)

    for path in medical_fixture_pdfs:
        result = await engine.extract(path, declared_content_type="application/pdf")
        assert result.extractor == ExtractorName.PYMUPDF.value, path.name
        assert result.quality_score >= 0.6, (
            f"{path.name} quality too low: {result.quality_score}"
        )
        assert result.character_count > 80, path.name
        assert result.page_count == 1
        # Searchable fixtures must not burn OCR/Vision.
        assert not any(
            attempt.extractor.value in {"tesseract", "gemini_vision"}
            and attempt.error is None
            and attempt.decision
            in {QualityDecision.ACCEPT, QualityDecision.ACCEPT_WITH_WARN}
            for attempt in result.fallbacks
        )


@pytest.mark.asyncio
async def test_extract_non_medical_decoys_still_yield_text(
    extraction_settings: Settings,
    non_medical_fixture_pdfs: list[Path],
) -> None:
    """Decoy docs must extract; AI classification later decides rejection."""
    engine = ExtractionEngine(extraction_settings)

    for path in non_medical_fixture_pdfs:
        result = await engine.extract(path, declared_content_type="application/pdf")
        assert result.character_count > 40, path.name
        assert result.quality_decision in {
            QualityDecision.ACCEPT,
            QualityDecision.ACCEPT_WITH_WARN,
        }


@pytest.mark.asyncio
async def test_extraction_cache_across_upload_copies(
    extraction_settings: Settings,
    medical_fixture_pdfs: list[Path],
) -> None:
    storage = LocalDocumentStorage(extraction_settings)
    engine = ExtractionEngine(extraction_settings)
    source = medical_fixture_pdfs[1]

    paths: list[Path] = []
    for _ in range(2):
        upload = make_upload_file(source)
        try:
            saved = await storage.save(
                user_id=uuid4(),
                family_member_id=uuid4(),
                upload=upload,
            )
        finally:
            await upload.close()
        paths.append(storage.resolve_path(saved.storage_path))

    first = await engine.extract(paths[0], declared_content_type="application/pdf")
    second = await engine.extract(paths[1], declared_content_type="application/pdf")

    assert first.cache_hit is False
    assert second.cache_hit is True
    assert first.file_sha256 == second.file_sha256
    assert first.text == second.text


@pytest.mark.asyncio
async def test_medvault_dummy_dataset_extraction_summary(
    extraction_settings: Settings,
    all_dummy_dataset_pdfs: list[Path],
) -> None:
    """Extract the full MedVault_Dummy_Dataset and write a summary report.

    Behavior protected:
    - Every dataset PDF extracts successfully through the engine.
    - Searchable medical PDFs prefer PyMuPDF.
    - Summary artifact is available for humans comparing quality.
    """
    engine = ExtractionEngine(extraction_settings)
    rows: list[ExtractionSummaryRow] = []

    for path in all_dummy_dataset_pdfs:
        result = await engine.extract(path, declared_content_type="application/pdf")
        rows.append(
            ExtractionSummaryRow(
                filename=path.name,
                category=_category_for(path),
                extractor=result.extractor,
                quality_score=round(result.quality_score, 4),
                quality_decision=result.quality_decision.value,
                confidence=round(result.confidence, 4),
                character_count=result.character_count,
                page_count=result.page_count,
                elapsed_ms=result.elapsed_ms,
                cache_hit=result.cache_hit,
                warnings=list(result.warnings),
                text_preview=result.text[:180].replace("\n", " "),
            )
        )

        assert result.character_count > 0, path.name
        assert result.extractor == ExtractorName.PYMUPDF.value, path.name
        assert result.quality_score >= 0.6, (
            f"{path.name} rejected by quality gate: {result.quality_score}"
        )

    by_decision: dict[str, int] = {}
    by_category: dict[str, int] = {}
    quality_scores = [row.quality_score for row in rows]
    for row in rows:
        by_decision[row.quality_decision] = by_decision.get(row.quality_decision, 0) + 1
        by_category[row.category] = by_category.get(row.category, 0) + 1

    summary = {
        "dataset": "MedVault_Dummy_Dataset",
        "document_count": len(rows),
        "extractor_used": ExtractorName.PYMUPDF.value,
        "quality": {
            "min": min(quality_scores),
            "max": max(quality_scores),
            "avg": round(sum(quality_scores) / len(quality_scores), 4),
        },
        "decisions": by_decision,
        "categories": by_category,
        "documents": [asdict(row) for row in rows],
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "medvault_dummy_dataset_extraction_summary.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    markdown_lines = [
        "# MedVault Dummy Dataset — Extraction Summary",
        "",
        f"- Documents: **{summary['document_count']}**",
        f"- Extractor: **{summary['extractor_used']}**",
        f"- Quality avg/min/max: "
        f"**{summary['quality']['avg']}** / "
        f"**{summary['quality']['min']}** / "
        f"**{summary['quality']['max']}**",
        f"- Decisions: `{by_decision}`",
        "",
        "| File | Category | Quality | Decision | Chars | Preview |",
        "|---|---|---:|---|---:|---|",
    ]
    for row in sorted(rows, key=lambda item: item.filename):
        preview = row.text_preview.replace("|", "/")[:80]
        markdown_lines.append(
            f"| `{row.filename}` | {row.category} | {row.quality_score:.3f} | "
            f"{row.quality_decision} | {row.character_count} | {preview} |"
        )

    md_path = OUTPUT_DIR / "medvault_dummy_dataset_extraction_summary.md"
    md_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    assert report_path.is_file()
    assert md_path.is_file()
    assert summary["document_count"] == len(all_dummy_dataset_pdfs)
    assert by_decision.get("reject", 0) == 0


@pytest.mark.asyncio
async def test_root_test_documents_extraction_summary(
    extraction_settings: Settings,
    test_documents_dir: Path,
) -> None:
    """Summarize the standalone Doe family reports under test-documents/."""
    engine = ExtractionEngine(extraction_settings)
    files = sorted(test_documents_dir.glob("*.pdf"))
    assert files, "Expected Doe-family PDFs in test-documents/"

    rows: list[dict] = []
    for path in files:
        result = await engine.extract(path, declared_content_type="application/pdf")
        rows.append(
            {
                "filename": path.name,
                "extractor": result.extractor,
                "quality_score": round(result.quality_score, 4),
                "quality_decision": result.quality_decision.value,
                "character_count": result.character_count,
                "text_preview": result.text[:160].replace("\n", " "),
            }
        )
        assert result.extractor == ExtractorName.PYMUPDF.value
        assert result.quality_score >= 0.6

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "test_documents_extraction_summary.json"
    path.write_text(
        json.dumps({"document_count": len(rows), "documents": rows}, indent=2),
        encoding="utf-8",
    )
    assert path.is_file()
    assert len(rows) == len(files)
