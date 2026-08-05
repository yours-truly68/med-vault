"""Text extraction from PDFs and images.

Native PDFs use embedded text layers via PyMuPDF. Pages with little or no
extractable text are treated as scanned and run through Tesseract OCR.
Scanned pages are OCR'd in parallel when multiple pages need it.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from app.core.config.settings import Settings

logger = logging.getLogger(__name__)

PDF_CONTENT_TYPE = "application/pdf"
IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})
PAGE_MARKER_TEMPLATE = "--- Page {page} ---\n"


@dataclass(frozen=True)
class OcrResult:
    text: str
    page_count: int


class OcrError(Exception):
    """Raised when text extraction fails."""


class OcrService:
    def __init__(self, settings: Settings) -> None:
        self._pdf_dpi = settings.ocr_pdf_dpi
        self._min_native_chars = settings.ocr_min_native_text_chars
        self._max_workers = max(1, settings.ocr_max_workers)
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_text(self, file_path: Path, content_type: str) -> str:
        return self.extract(file_path, content_type).text

    def extract(self, file_path: Path, content_type: str) -> OcrResult:
        if not file_path.is_file():
            raise OcrError(f"File not found: {file_path}")

        normalized_type = content_type.split(";", 1)[0].strip().lower()

        if normalized_type == PDF_CONTENT_TYPE:
            return self._extract_from_pdf(file_path)
        if normalized_type in IMAGE_CONTENT_TYPES:
            return self._extract_from_image(file_path)

        raise OcrError(f"Unsupported content type for OCR: {content_type}")

    def get_page_count(self, file_path: Path, content_type: str) -> int:
        normalized_type = content_type.split(";", 1)[0].strip().lower()
        if normalized_type == PDF_CONTENT_TYPE:
            with pymupdf.open(file_path) as document:
                return max(document.page_count, 1)
        if normalized_type in IMAGE_CONTENT_TYPES:
            return 1
        return 1

    def _extract_from_pdf(self, file_path: Path) -> OcrResult:
        try:
            with pymupdf.open(file_path) as document:
                if document.page_count == 0:
                    raise OcrError("PDF has no pages")

                page_texts: list[str | None] = [None] * document.page_count
                ocr_page_indices: list[int] = []

                for page in document:
                    native_text = page.get_text().strip()
                    if len(native_text) >= self._min_native_chars:
                        page_texts[page.number] = native_text
                        continue

                    logger.debug(
                        "Page %s of %s has little native text; queuing OCR",
                        page.number + 1,
                        file_path.name,
                    )
                    ocr_page_indices.append(page.number)

                if ocr_page_indices:
                    self._ocr_pages_parallel(file_path, ocr_page_indices, page_texts)

                resolved = [text for text in page_texts if text]
                if not resolved:
                    raise OcrError("No text could be extracted from PDF")

                return OcrResult(
                    text=self._join_page_texts(resolved),
                    page_count=document.page_count,
                )
        except OcrError:
            raise
        except Exception as exc:
            raise OcrError(f"Failed to process PDF: {exc}") from exc

    def _ocr_pages_parallel(
        self,
        file_path: Path,
        page_indices: list[int],
        page_texts: list[str | None],
    ) -> None:
        if len(page_indices) == 1:
            page_texts[page_indices[0]] = self._ocr_page_by_index(file_path, page_indices[0])
            return

        workers = min(self._max_workers, len(page_indices))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(self._ocr_page_by_index, file_path, index): index
                for index in page_indices
            }
            for future in as_completed(futures):
                index = futures[future]
                page_texts[index] = future.result()

    def _ocr_page_by_index(self, file_path: Path, page_index: int) -> str:
        try:
            with pymupdf.open(file_path) as document:
                return self._ocr_page(document[page_index])
        except Exception as exc:
            raise OcrError(f"Failed to OCR PDF page {page_index + 1}: {exc}") from exc

    def _extract_from_image(self, file_path: Path) -> OcrResult:
        try:
            with Image.open(file_path) as image:
                text = pytesseract.image_to_string(image).strip()
        except OcrError:
            raise
        except Exception as exc:
            raise OcrError(f"Failed to OCR image: {exc}") from exc

        if not text:
            raise OcrError("No text could be extracted from image")

        return OcrResult(
            text=PAGE_MARKER_TEMPLATE.format(page=1) + text,
            page_count=1,
        )

    def _ocr_page(self, page: pymupdf.Page) -> str:
        try:
            pixmap = page.get_pixmap(dpi=self._pdf_dpi)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            return pytesseract.image_to_string(image).strip()
        except Exception as exc:
            raise OcrError(f"Failed to OCR PDF page {page.number + 1}: {exc}") from exc

    def _join_page_texts(self, page_texts: list[str]) -> str:
        non_empty = [text for text in page_texts if text]
        if not non_empty:
            raise OcrError("No text could be extracted from PDF")

        blocks: list[str] = []
        for index, text in enumerate(non_empty, start=1):
            blocks.append(PAGE_MARKER_TEMPLATE.format(page=index) + text)
        return "\n\n".join(blocks)
