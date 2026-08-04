"""Text extraction from PDFs and images.

Native PDFs use embedded text layers via PyMuPDF. Pages with little or no
extractable text are treated as scanned and run through Tesseract OCR.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pymupdf
import pytesseract
from PIL import Image

from app.core.config.settings import Settings

logger = logging.getLogger(__name__)

PDF_CONTENT_TYPE = "application/pdf"
IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/png"})


class OcrError(Exception):
    """Raised when text extraction fails."""


class OcrService:
    def __init__(self, settings: Settings) -> None:
        self._pdf_dpi = settings.ocr_pdf_dpi
        self._min_native_chars = settings.ocr_min_native_text_chars
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_text(self, file_path: Path, content_type: str) -> str:
        if not file_path.is_file():
            raise OcrError(f"File not found: {file_path}")

        normalized_type = content_type.split(";", 1)[0].strip().lower()

        if normalized_type == PDF_CONTENT_TYPE:
            return self._extract_from_pdf(file_path)
        if normalized_type in IMAGE_CONTENT_TYPES:
            return self._extract_from_image(file_path)

        raise OcrError(f"Unsupported content type for OCR: {content_type}")

    def _extract_from_pdf(self, file_path: Path) -> str:
        try:
            with pymupdf.open(file_path) as document:
                if document.page_count == 0:
                    raise OcrError("PDF has no pages")

                page_texts: list[str] = []
                for page in document:
                    native_text = page.get_text().strip()
                    if len(native_text) >= self._min_native_chars:
                        page_texts.append(native_text)
                        continue

                    logger.debug(
                        "Page %s of %s has little native text; running OCR",
                        page.number + 1,
                        file_path.name,
                    )
                    page_texts.append(self._ocr_page(page))

                return self._join_page_texts(page_texts)
        except OcrError:
            raise
        except Exception as exc:
            raise OcrError(f"Failed to process PDF: {exc}") from exc

    def _extract_from_image(self, file_path: Path) -> str:
        try:
            with Image.open(file_path) as image:
                text = pytesseract.image_to_string(image).strip()
        except OcrError:
            raise
        except Exception as exc:
            raise OcrError(f"Failed to OCR image: {exc}") from exc

        if not text:
            raise OcrError("No text could be extracted from image")

        return text

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

        return "\n\n".join(non_empty)
