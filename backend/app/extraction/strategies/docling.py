"""Docling layout-aware PDF extraction (optional dependency)."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import ClassVar

from app.core.config.settings import Settings
from app.extraction.exceptions import EmptyExtractionError, ExtractorUnavailableError
from app.extraction.models import (
    ExtractionRequest,
    ExtractorHealth,
    ExtractorName,
    FileKind,
    FileProbe,
    RawExtraction,
)
from app.extraction.strategies.base import BaseExtractor

logger = logging.getLogger(__name__)


class DoclingExtractor(BaseExtractor):
    name: ClassVar[ExtractorName] = ExtractorName.DOCLING

    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.docling_enabled
        self._timeout = settings.docling_timeout_seconds

    def supports(self, probe: FileProbe) -> bool:
        return self._enabled and probe.kind == FileKind.PDF

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        if not self._enabled:
            raise ExtractorUnavailableError("Docling is disabled")
        return await asyncio.wait_for(
            asyncio.to_thread(self._extract_sync, request),
            timeout=self._timeout,
        )

    async def health_check(self) -> ExtractorHealth:
        if not self._enabled:
            return ExtractorHealth(
                name=self.name,
                healthy=False,
                detail="disabled",
            )
        started = time.perf_counter()
        try:
            import docling  # noqa: F401

            return ExtractorHealth(
                name=self.name,
                healthy=True,
                detail="docling import ok",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except ImportError as exc:
            return ExtractorHealth(name=self.name, healthy=False, detail=str(exc))

    def _extract_sync(self, request: ExtractionRequest) -> RawExtraction:
        try:
            from docling.document_converter import DocumentConverter
        except ImportError as exc:
            raise ExtractorUnavailableError(
                "Docling is not installed. Install with: pip install 'medvault-backend[docling]'"
            ) from exc

        try:
            converter = DocumentConverter()
            result = converter.convert(str(request.path))
            text = result.document.export_to_markdown().strip()
        except ExtractorUnavailableError:
            raise
        except Exception as exc:
            raise ExtractorUnavailableError(f"Docling extraction failed: {exc}") from exc

        if not text:
            raise EmptyExtractionError("Docling returned empty text")

        page_count = request.probe.page_count_hint or 1
        return RawExtraction(
            text=text,
            page_count=page_count,
            extractor_confidence=0.85,
            warnings=["docling_markdown_export"],
        )
