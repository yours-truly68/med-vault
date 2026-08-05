"""Tests for Extraction Engine routing, quality scoring, and fallbacks."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar
from uuid import uuid4

import pymupdf
import pytest
from PIL import Image, ImageDraw

from app.core.config.settings import Settings
from app.extraction.cache import ExtractionCache
from app.extraction.engine import ExtractionEngine
from app.extraction.exceptions import AllExtractorsFailedError, CorruptFileError
from app.extraction.models import (
    ExtractionRequest,
    ExtractorHealth,
    ExtractorName,
    FileKind,
    FileProbe,
    QualityDecision,
    RawExtraction,
)
from app.extraction.quality import QualityScorer
from app.extraction.router import ExtractionRouter
from app.extraction.strategies.base import BaseExtractor


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        extraction_cache_dir=str(tmp_path / "cache"),
        extraction_cache_enabled=True,
        docling_enabled=False,
        gemini_vision_enabled=False,
        vision_fallback=None,
        primary_pdf_extractor="pymupdf",
        secondary_pdf_extractor=None,
        image_extractor="tesseract",
        tesseract_enabled=True,
        extraction_quality_accept_threshold=0.9,
        extraction_quality_warn_threshold=0.6,
    )


def _write_searchable_pdf(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Patient Name: Jane Doe\nDiagnosis: Hypertension\nPrescription: Amlodipine 5 mg\n"
        "Hospital Lab Report Creatinine Glucose Hemoglobin",
        fontsize=12,
    )
    doc.save(path)
    doc.close()


def _write_empty_pdf(path: Path) -> None:
    doc = pymupdf.open()
    doc.new_page()
    doc.save(path)
    doc.close()


def _write_image(path: Path, text: str = "Rx Patient Dosage 10 mg") -> None:
    image = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 40), text, fill=(0, 0, 0))
    image.save(path)


class FakeExtractor(BaseExtractor):
    name: ClassVar[ExtractorName] = ExtractorName.PYMUPDF

    def __init__(
        self,
        *,
        text: str = "",
        fail: bool = False,
        confidence: float = 1.0,
        kinds: set[FileKind] | None = None,
    ) -> None:
        self._text = text
        self._fail = fail
        self._confidence = confidence
        self._kinds = kinds or {FileKind.PDF, FileKind.IMAGE}
        self.calls = 0

    def supports(self, probe: FileProbe) -> bool:
        return probe.kind in self._kinds

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        self.calls += 1
        if self._fail:
            raise RuntimeError(f"{self.name} failed")
        if not self._text.strip():
            from app.extraction.exceptions import EmptyExtractionError

            raise EmptyExtractionError("empty")
        return RawExtraction(
            text=self._text,
            page_count=1,
            extractor_confidence=self._confidence,
        )

    async def health_check(self) -> ExtractorHealth:
        return ExtractorHealth(name=self.name, healthy=True)


def _fake(
    extractor_name: ExtractorName,
    *,
    text: str = "",
    fail: bool = False,
    confidence: float = 1.0,
    kinds: set[FileKind] | None = None,
) -> FakeExtractor:
    class _NamedFake(FakeExtractor):
        name = extractor_name

    return _NamedFake(text=text, fail=fail, confidence=confidence, kinds=kinds)


class TestQualityScorer:
    def test_empty_text_rejects(self) -> None:
        scorer = QualityScorer()
        score = scorer.score(RawExtraction(text="   ", page_count=1))
        assert score.decision == QualityDecision.REJECT
        assert score.score == 0.0

    def test_medical_text_accepts(self) -> None:
        scorer = QualityScorer()
        text = (
            "Patient diagnosis prescription dosage hospital doctor lab "
            "hemoglobin creatinine medication mg ml report findings treatment"
        )
        score = scorer.score(
            RawExtraction(text=text * 3, page_count=1, extractor_confidence=1.0),
            is_ocr=False,
        )
        assert score.score >= 0.6
        assert score.decision in {
            QualityDecision.ACCEPT,
            QualityDecision.ACCEPT_WITH_WARN,
        }

    def test_garbled_text_low_score(self) -> None:
        scorer = QualityScorer()
        garbled = "xqzvwrtplkjhgfds " * 40 + "@@@@ #### %%%%"
        score = scorer.score(RawExtraction(text=garbled, page_count=1), is_ocr=True)
        assert score.score < 0.9


class TestExtractionRouter:
    def test_image_plan(self, settings: Settings) -> None:
        router = ExtractionRouter(settings)
        probe = FileProbe(
            path=Path("x.png"),
            kind=FileKind.IMAGE,
            mime_type="image/png",
            size_bytes=10,
            file_sha256="a" * 64,
        )
        assert router.plan(probe) == [ExtractorName.TESSERACT]

    def test_searchable_pdf_plan(self, settings: Settings) -> None:
        router = ExtractionRouter(settings)
        probe = FileProbe(
            path=Path("x.pdf"),
            kind=FileKind.PDF,
            mime_type="application/pdf",
            size_bytes=10,
            file_sha256="b" * 64,
            is_searchable_pdf=True,
        )
        assert router.plan(probe)[0] == ExtractorName.PYMUPDF
        assert ExtractorName.TESSERACT in router.plan(probe)

    def test_vision_fallback_appended_when_configured(self, tmp_path: Path) -> None:
        settings = Settings(
            extraction_cache_dir=str(tmp_path / "cache"),
            vision_fallback="gemini",
            image_extractor="tesseract",
            primary_pdf_extractor="pymupdf",
            gemini_api_key="test-key",
            vision_provider="gemini",
            vision_model="gemini-2.0-flash",
            docling_enabled=False,
        )
        router = ExtractionRouter(settings)
        probe = FileProbe(
            path=Path("x.png"),
            kind=FileKind.IMAGE,
            mime_type="image/png",
            size_bytes=10,
            file_sha256="c" * 64,
        )
        assert router.plan(probe) == [
            ExtractorName.TESSERACT,
            ExtractorName.GEMINI_VISION,
        ]


class TestExtractionEngine:
    @pytest.mark.asyncio
    async def test_searchable_pdf_uses_pymupdf(self, settings: Settings, tmp_path: Path) -> None:
        pdf = tmp_path / "lab.pdf"
        _write_searchable_pdf(pdf)

        pymupdf_extractor = _fake(
            ExtractorName.PYMUPDF,
            text="Patient diagnosis prescription hospital lab hemoglobin creatinine dosage mg",
            kinds={FileKind.PDF},
        )
        tesseract = _fake(
            ExtractorName.TESSERACT,
            text="should not run",
            kinds={FileKind.PDF, FileKind.IMAGE},
        )
        engine = ExtractionEngine(
            settings,
            extractors={
                ExtractorName.PYMUPDF: pymupdf_extractor,
                ExtractorName.TESSERACT: tesseract,
                ExtractorName.DOCLING: _fake(
                    ExtractorName.DOCLING, fail=True, kinds={FileKind.PDF}
                ),
                ExtractorName.GEMINI_VISION: _fake(
                    ExtractorName.GEMINI_VISION, fail=True
                ),
            },
        )

        result = await engine.extract(pdf, declared_content_type="application/pdf")
        assert result.extractor == ExtractorName.PYMUPDF.value
        assert pymupdf_extractor.calls == 1
        assert tesseract.calls == 0
        assert result.quality_score >= 0.6

    @pytest.mark.asyncio
    async def test_fallback_on_poor_quality(self, settings: Settings, tmp_path: Path) -> None:
        pdf = tmp_path / "scan.pdf"
        _write_empty_pdf(pdf)

        weak = _fake(
            ExtractorName.PYMUPDF,
            text="@@",
            confidence=0.1,
            kinds={FileKind.PDF},
        )
        strong = _fake(
            ExtractorName.TESSERACT,
            text=(
                "Patient diagnosis prescription hospital lab hemoglobin "
                "creatinine dosage medication doctor report findings"
            ),
            confidence=0.9,
            kinds={FileKind.PDF, FileKind.IMAGE},
        )
        engine = ExtractionEngine(
            settings,
            extractors={
                ExtractorName.PYMUPDF: weak,
                ExtractorName.TESSERACT: strong,
                ExtractorName.DOCLING: _fake(
                    ExtractorName.DOCLING, fail=True, kinds={FileKind.PDF}
                ),
                ExtractorName.GEMINI_VISION: _fake(
                    ExtractorName.GEMINI_VISION, fail=True
                ),
            },
        )

        result = await engine.extract(pdf, declared_content_type="application/pdf")
        assert result.extractor == ExtractorName.TESSERACT.value
        assert weak.calls == 1
        assert strong.calls == 1
        assert len(result.fallbacks) >= 2

    @pytest.mark.asyncio
    async def test_cache_hit(self, settings: Settings, tmp_path: Path) -> None:
        pdf = tmp_path / "cached.pdf"
        _write_searchable_pdf(pdf)

        extractor = _fake(
            ExtractorName.PYMUPDF,
            text=(
                "Patient diagnosis prescription hospital lab hemoglobin "
                "creatinine dosage medication doctor report findings treatment"
            ),
            kinds={FileKind.PDF},
        )
        engine = ExtractionEngine(
            settings,
            extractors={
                ExtractorName.PYMUPDF: extractor,
                ExtractorName.TESSERACT: _fake(ExtractorName.TESSERACT, fail=True),
                ExtractorName.DOCLING: _fake(ExtractorName.DOCLING, fail=True),
                ExtractorName.GEMINI_VISION: _fake(
                    ExtractorName.GEMINI_VISION, fail=True
                ),
            },
        )

        first = await engine.extract(pdf, declared_content_type="application/pdf")
        second = await engine.extract(pdf, declared_content_type="application/pdf")
        assert first.cache_hit is False
        assert second.cache_hit is True
        assert extractor.calls == 1

    @pytest.mark.asyncio
    async def test_corrupt_pdf_raises(self, settings: Settings, tmp_path: Path) -> None:
        path = tmp_path / "bad.pdf"
        path.write_bytes(b"%PDF-1.4 broken")
        engine = ExtractionEngine(settings)
        with pytest.raises((CorruptFileError, AllExtractorsFailedError)):
            await engine.extract(path, declared_content_type="application/pdf")

    @pytest.mark.asyncio
    async def test_real_pymupdf_searchable_pdf(self, settings: Settings, tmp_path: Path) -> None:
        pdf = tmp_path / "real.pdf"
        _write_searchable_pdf(pdf)
        engine = ExtractionEngine(settings)
        result = await engine.extract(
            pdf,
            declared_content_type="application/pdf",
            document_id=uuid4(),
        )
        assert "Patient" in result.text
        assert result.extractor == ExtractorName.PYMUPDF.value
        assert result.page_count == 1


class TestExtractionCache:
    def test_hash_stable(self, tmp_path: Path) -> None:
        path = tmp_path / "a.bin"
        path.write_bytes(b"hello")
        assert ExtractionCache.hash_file(path) == ExtractionCache.hash_file(path)
