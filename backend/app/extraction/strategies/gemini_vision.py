"""Vision-based last-resort extractor driven by VISION_* AI routing."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import ClassVar

import pymupdf

from app.ai.config import AITask, resolve_provider_credentials
from app.ai.providers.base import ProviderError
from app.ai.router import AITaskRouter, create_ai_router
from app.core.config.settings import Settings
from app.extraction.exceptions import EmptyExtractionError, ExtractorUnavailableError
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
VISION_PROMPT = (
    "Extract all readable text from this medical document image. "
    "Preserve structure, headings, tables, and lab values when possible. "
    "Return plain text only."
)


class GeminiVisionExtractor(BaseExtractor):
    name: ClassVar[ExtractorName] = ExtractorName.GEMINI_VISION

    def __init__(self, settings: Settings, *, router: AITaskRouter | None = None) -> None:
        self._settings = settings
        self._router = router or create_ai_router(settings)
        self._max_pages = settings.gemini_vision_max_pages
        self._pdf_dpi = min(settings.ocr_pdf_dpi, 150)
        self._enabled = bool(settings.vision_fallback and settings.vision_fallback.strip())

    def supports(self, probe: FileProbe) -> bool:
        if not self._enabled:
            return False
        if probe.kind not in {FileKind.PDF, FileKind.IMAGE}:
            return False
        try:
            route = self._router.route_for(AITask.VISION)
            resolve_provider_credentials(self._settings, route.provider)
        except (ValueError, KeyError):
            return False
        return True

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        if not self.supports(request.probe):
            raise ExtractorUnavailableError("Vision fallback extractor is not configured")

        if request.probe.kind == FileKind.IMAGE:
            text = await self._extract_image_bytes(request.path.read_bytes(), mime="image/jpeg")
            if not text.strip():
                raise EmptyExtractionError("Vision extractor returned empty text")
            return RawExtraction(
                text=PAGE_MARKER_TEMPLATE.format(page=1) + text.strip(),
                page_count=1,
                page_results=[
                    PageExtraction(
                        page_number=1,
                        text=text.strip(),
                        char_count=len(text.strip()),
                        ocr_confidence=0.7,
                        source=self.name,
                    )
                ],
                extractor_confidence=0.7,
                warnings=["vision_fallback"],
            )

        return await self._extract_pdf(request.path)

    async def health_check(self) -> ExtractorHealth:
        if not self._enabled:
            return ExtractorHealth(name=self.name, healthy=False, detail="disabled")

        route = self._router.route_for(AITask.VISION)
        health = await self._router.health_check_task(AITask.VISION)
        detail = f"provider={route.provider} model={route.model} {health.detail}"
        return ExtractorHealth(name=self.name, healthy=health.healthy, detail=detail)

    async def _extract_pdf(self, path: Path) -> RawExtraction:
        images = await asyncio.to_thread(self._pdf_to_png_bytes, path)
        if not images:
            raise EmptyExtractionError("No pages available for vision extraction")

        page_results: list[PageExtraction] = []
        blocks: list[str] = []
        for index, png_bytes in enumerate(images, start=1):
            text = (await self._extract_image_bytes(png_bytes, mime="image/png")).strip()
            page_results.append(
                PageExtraction(
                    page_number=index,
                    text=text,
                    char_count=len(text),
                    ocr_confidence=0.7,
                    source=self.name,
                )
            )
            if text:
                blocks.append(PAGE_MARKER_TEMPLATE.format(page=index) + text)

        if not blocks:
            raise EmptyExtractionError("Vision extractor returned empty text for PDF")

        return RawExtraction(
            text="\n\n".join(blocks),
            page_count=len(images),
            page_results=page_results,
            extractor_confidence=0.7,
            warnings=["vision_fallback"],
        )

    def _pdf_to_png_bytes(self, path: Path) -> list[bytes]:
        images: list[bytes] = []
        with pymupdf.open(path) as document:
            limit = min(document.page_count, self._max_pages)
            for index in range(limit):
                pixmap = document[index].get_pixmap(dpi=self._pdf_dpi)
                images.append(pixmap.tobytes("png"))
        return images

    async def _extract_image_bytes(self, image_bytes: bytes, *, mime: str) -> str:
        started = time.perf_counter()
        try:
            result = await self._router.vision(
                VISION_PROMPT,
                image_bytes,
                mime_type=mime,
                temperature=0.0,
            )
        except ProviderError as exc:
            raise ExtractorUnavailableError(f"Vision OCR failed: {exc}") from exc

        elapsed = (time.perf_counter() - started) * 1000
        logger.info(
            "Vision OCR completed in %.0fms (provider=%s model=%s)",
            elapsed,
            result.provider,
            result.model,
        )
        return result.content
