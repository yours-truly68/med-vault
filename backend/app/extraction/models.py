"""Pydantic models for the Extraction Engine."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from uuid import UUID

from pydantic import BaseModel, Field


class ExtractorName(StrEnum):
    PYMUPDF = "pymupdf"
    DOCLING = "docling"
    TESSERACT = "tesseract"
    GEMINI_VISION = "gemini_vision"  # Deprecated in MVP


class FileKind(StrEnum):
    PDF = "pdf"
    IMAGE = "image"
    UNKNOWN = "unknown"


class QualityDecision(StrEnum):
    ACCEPT = "accept"
    ACCEPT_WITH_WARN = "accept_with_warn"
    REJECT = "reject"


class FileProbe(BaseModel):
    """Inspection result — no OCR performed."""

    path: Path
    kind: FileKind
    mime_type: str
    size_bytes: int
    file_sha256: str
    page_count_hint: int | None = None
    is_searchable_pdf: bool | None = None
    declared_content_type: str | None = None
    width: int | None = None
    height: int | None = None
    extension: str | None = None
    pdf_metadata: dict[str, str] = Field(default_factory=dict)
    estimated_ocr_required: bool = False


class PageExtraction(BaseModel):
    page_number: int
    text: str
    char_count: int
    ocr_confidence: float | None = None
    source: ExtractorName


class RawExtraction(BaseModel):
    """Pre-quality output from a single strategy."""

    text: str
    page_count: int
    page_results: list[PageExtraction] = Field(default_factory=list)
    extractor_confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)


class QualityComponents(BaseModel):
    printable_ratio: float
    ocr_confidence: float
    text_density: float
    medical_keyword_score: float
    garbled_penalty: float


class QualityScore(BaseModel):
    score: float
    decision: QualityDecision
    components: QualityComponents
    reasons: list[str] = Field(default_factory=list)


class FallbackAttempt(BaseModel):
    extractor: ExtractorName
    duration_ms: float
    quality_score: float | None = None
    error: str | None = None
    decision: QualityDecision | None = None


class ExtractionResult(BaseModel):
    """Unified extraction output — AI pipeline input."""

    text: str
    extractor: str
    confidence: float
    quality_score: float
    quality_decision: QualityDecision
    character_count: int
    page_count: int
    elapsed_ms: int
    warnings: list[str] = Field(default_factory=list)
    quality: QualityScore | None = None
    fallbacks: list[FallbackAttempt] = Field(default_factory=list)
    cache_hit: bool = False
    file_sha256: str = ""
    page_results: list[PageExtraction] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
    path: Path
    probe: FileProbe
    document_id: UUID | None = None


class ExtractorHealth(BaseModel):
    name: ExtractorName
    healthy: bool
    detail: str | None = None
    latency_ms: float | None = None


class ExtractionHealthReport(BaseModel):
    healthy: bool
    extractors: list[ExtractorHealth]
