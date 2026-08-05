"""PyMuPDF native text extraction for searchable PDFs."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import ClassVar

import pymupdf

from app.core.config.settings import Settings
from app.extraction.exceptions import CorruptFileError, EmptyExtractionError
from app.extraction.models import (
    ExtractionRequest,
    ExtractorHealth,
    ExtractorName,
    FileKind,
    FileProbe,
    PageExtraction,
    RawExtraction,
)
from app.extraction.strategies.base import BaseExtractor

logger = logging.getLogger(__name__)

PAGE_MARKER_TEMPLATE = "--- Page {page} ---\n"


class PyMuPdfExtractor(BaseExtractor):
    name: ClassVar[ExtractorName] = ExtractorName.PYMUPDF

    def __init__(self, settings: Settings) -> None:
        self._min_native_chars = settings.ocr_min_native_text_chars

    def supports(self, probe: FileProbe) -> bool:
        return probe.kind == FileKind.PDF

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        return await asyncio.to_thread(self._extract_sync, request)

    async def health_check(self) -> ExtractorHealth:
        started = time.perf_counter()
        try:
            _ = pymupdf.version
            return ExtractorHealth(
                name=self.name,
                healthy=True,
                detail=f"pymupdf {pymupdf.version[0]}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            return ExtractorHealth(name=self.name, healthy=False, detail=str(exc))

    def _extract_sync(self, request: ExtractionRequest) -> RawExtraction:
        path = request.path
        try:
            with pymupdf.open(path) as document:
                if document.page_count == 0:
                    raise EmptyExtractionError("PDF has no pages")

                page_results: list[PageExtraction] = []
                weak_pages = 0
                for page in document:
                    text = page.get_text().strip()
                    if len(text) < self._min_native_chars:
                        weak_pages += 1
                    page_results.append(
                        PageExtraction(
                            page_number=page.number + 1,
                            text=text,
                            char_count=len(text),
                            ocr_confidence=None,
                            source=self.name,
                        )
                    )

                blocks = [
                    PAGE_MARKER_TEMPLATE.format(page=item.page_number) + item.text
                    for item in page_results
                    if item.text
                ]
                if not blocks:
                    raise EmptyExtractionError("No native text layer found in PDF")

                warnings: list[str] = []
                if weak_pages:
                    warnings.append(f"{weak_pages}_pages_below_native_text_threshold")

                return RawExtraction(
                    text="\n\n".join(blocks),
                    page_count=document.page_count,
                    page_results=page_results,
                    extractor_confidence=1.0,
                    warnings=warnings,
                )
        except (EmptyExtractionError, CorruptFileError):
            raise
        except Exception as exc:
            raise CorruptFileError(f"Failed to open PDF with PyMuPDF: {exc}") from exc
