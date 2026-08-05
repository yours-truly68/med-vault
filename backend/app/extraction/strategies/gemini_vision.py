"""Gemini Vision last-resort extractor (optional, expensive)."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import ClassVar

import httpx
import pymupdf

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

    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.gemini_vision_enabled
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_vision_model
        self._timeout = settings.gemini_vision_timeout_seconds
        self._max_pages = settings.gemini_vision_max_pages
        self._pdf_dpi = min(settings.ocr_pdf_dpi, 150)

    def supports(self, probe: FileProbe) -> bool:
        return (
            self._enabled
            and bool(self._api_key)
            and probe.kind in {FileKind.PDF, FileKind.IMAGE}
        )

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        if not self.supports(request.probe):
            raise ExtractorUnavailableError("Gemini Vision is not configured")

        if request.probe.kind == FileKind.IMAGE:
            text = await self._extract_image_bytes(request.path.read_bytes(), mime="image/jpeg")
            if not text.strip():
                raise EmptyExtractionError("Gemini Vision returned empty text")
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
                warnings=["gemini_vision_fallback"],
            )

        return await self._extract_pdf(request.path)

    async def health_check(self) -> ExtractorHealth:
        if not self._enabled or not self._api_key:
            return ExtractorHealth(name=self.name, healthy=False, detail="disabled_or_missing_key")
        return ExtractorHealth(name=self.name, healthy=True, detail=f"model={self._model}")

    async def _extract_pdf(self, path: Path) -> RawExtraction:
        images = await asyncio.to_thread(self._pdf_to_png_bytes, path)
        if not images:
            raise EmptyExtractionError("No pages available for Gemini Vision")

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
            raise EmptyExtractionError("Gemini Vision returned empty text for PDF")

        return RawExtraction(
            text="\n\n".join(blocks),
            page_count=len(images),
            page_results=page_results,
            extractor_confidence=0.7,
            warnings=["gemini_vision_fallback"],
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
        assert self._api_key is not None
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": VISION_PROMPT},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {"temperature": 0.0},
        }
        started = time.perf_counter()
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                url,
                params={"key": self._api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        elapsed = (time.perf_counter() - started) * 1000
        logger.info("Gemini Vision call completed in %.0fms", elapsed)

        try:
            parts = data["candidates"][0]["content"]["parts"]
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            return "\n".join(text for text in texts if text).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ExtractorUnavailableError(
                f"Unexpected Gemini Vision response shape: {exc}"
            ) from exc
