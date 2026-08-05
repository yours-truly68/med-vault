"""Tesseract OCR for images and scanned PDF pages."""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import ClassVar

import pymupdf
import pytesseract
from PIL import Image

from app.core.config.settings import Settings
from app.extraction.exceptions import CorruptFileError, EmptyExtractionError, ExtractorUnavailableError
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


class TesseractExtractor(BaseExtractor):
    name: ClassVar[ExtractorName] = ExtractorName.TESSERACT

    def __init__(self, settings: Settings) -> None:
        self._enabled = settings.tesseract_enabled
        self._pdf_dpi = settings.ocr_pdf_dpi
        self._max_workers = max(1, settings.ocr_max_workers)
        self._ocr_language = settings.ocr_language
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def supports(self, probe: FileProbe) -> bool:
        return self._enabled and probe.kind in {FileKind.PDF, FileKind.IMAGE}

    async def extract(self, request: ExtractionRequest) -> RawExtraction:
        return await asyncio.to_thread(self._extract_sync, request)

    async def health_check(self) -> ExtractorHealth:
        if not self._enabled:
            return ExtractorHealth(name=self.name, healthy=False, detail="disabled")
        started = time.perf_counter()
        try:
            version = await asyncio.to_thread(pytesseract.get_tesseract_version)
            return ExtractorHealth(
                name=self.name,
                healthy=True,
                detail=f"tesseract {version}",
                latency_ms=(time.perf_counter() - started) * 1000,
            )
        except Exception as exc:
            return ExtractorHealth(name=self.name, healthy=False, detail=str(exc))

    def _extract_sync(self, request: ExtractionRequest) -> RawExtraction:
        probe = request.probe
        if probe.kind == FileKind.IMAGE:
            return self._extract_image(request.path)
        if probe.kind == FileKind.PDF:
            return self._extract_pdf(request.path)
        raise ExtractorUnavailableError(f"Tesseract does not support {probe.kind}")

    def _extract_image(self, path) -> RawExtraction:
        try:
            with Image.open(path) as image:
                data = pytesseract.image_to_data(
                    image,
                    lang=self._ocr_language,
                    output_type=pytesseract.Output.DICT,
                )
                text = pytesseract.image_to_string(image, lang=self._ocr_language).strip()
                confidence = self._mean_confidence(data)
        except Exception as exc:
            raise CorruptFileError(f"Failed to OCR image: {exc}") from exc

        if not text:
            raise EmptyExtractionError("No text could be extracted from image")

        return RawExtraction(
            text=PAGE_MARKER_TEMPLATE.format(page=1) + text,
            page_count=1,
            page_results=[
                PageExtraction(
                    page_number=1,
                    text=text,
                    char_count=len(text),
                    ocr_confidence=confidence,
                    source=self.name,
                )
            ],
            extractor_confidence=confidence,
        )

    def _extract_pdf(self, path) -> RawExtraction:
        try:
            with pymupdf.open(path) as document:
                if document.page_count == 0:
                    raise EmptyExtractionError("PDF has no pages")
                page_indices = list(range(document.page_count))
        except EmptyExtractionError:
            raise
        except Exception as exc:
            raise CorruptFileError(f"Failed to open PDF for OCR: {exc}") from exc

        page_texts: dict[int, tuple[str, float | None]] = {}
        if len(page_indices) == 1:
            text, conf = self._ocr_pdf_page(path, page_indices[0])
            page_texts[page_indices[0]] = (text, conf)
        else:
            workers = min(self._max_workers, len(page_indices))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {
                    executor.submit(self._ocr_pdf_page, path, index): index
                    for index in page_indices
                }
                for future in as_completed(futures):
                    index = futures[future]
                    page_texts[index] = future.result()

        page_results: list[PageExtraction] = []
        confidences: list[float] = []
        blocks: list[str] = []
        for index in sorted(page_texts):
            text, conf = page_texts[index]
            if conf is not None:
                confidences.append(conf)
            page_results.append(
                PageExtraction(
                    page_number=index + 1,
                    text=text,
                    char_count=len(text),
                    ocr_confidence=conf,
                    source=self.name,
                )
            )
            if text:
                blocks.append(PAGE_MARKER_TEMPLATE.format(page=index + 1) + text)

        if not blocks:
            raise EmptyExtractionError("No text could be OCR'd from PDF")

        mean_conf = sum(confidences) / len(confidences) if confidences else None
        return RawExtraction(
            text="\n\n".join(blocks),
            page_count=len(page_indices),
            page_results=page_results,
            extractor_confidence=mean_conf,
        )

    def _ocr_pdf_page(self, path, page_index: int) -> tuple[str, float | None]:
        try:
            with pymupdf.open(path) as document:
                page = document[page_index]
                pixmap = page.get_pixmap(dpi=self._pdf_dpi)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                data = pytesseract.image_to_data(
                    image,
                    lang=self._ocr_language,
                    output_type=pytesseract.Output.DICT,
                )
                text = pytesseract.image_to_string(image, lang=self._ocr_language).strip()
                return text, self._mean_confidence(data)
        except Exception as exc:
            raise CorruptFileError(f"Failed to OCR PDF page {page_index + 1}: {exc}") from exc

    def _mean_confidence(self, data: dict) -> float | None:
        confs = []
        for value in data.get("conf", []):
            try:
                conf = float(value)
            except (TypeError, ValueError):
                continue
            if conf >= 0:
                confs.append(conf)
        if not confs:
            return None
        return (sum(confs) / len(confs)) / 100.0
