"""Extraction router — builds ordered strategy chains from inspection signals."""

from __future__ import annotations

from app.core.config.settings import Settings
from app.extraction.exceptions import UnsupportedFileError
from app.extraction.models import ExtractorName, FileKind, FileProbe


class ExtractionRouter:
    """Decides extractor order. Does not run extractors."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(self, probe: FileProbe) -> list[ExtractorName]:
        if probe.kind == FileKind.IMAGE:
            chain = [ExtractorName.TESSERACT]
            if self._gemini_available():
                chain.append(ExtractorName.GEMINI_VISION)
            return chain

        if probe.kind == FileKind.PDF:
            chain: list[ExtractorName] = []
            if probe.is_searchable_pdf:
                chain.append(ExtractorName.PYMUPDF)
            if self._settings.docling_enabled:
                chain.append(ExtractorName.DOCLING)
            chain.append(ExtractorName.TESSERACT)
            if self._gemini_available():
                chain.append(ExtractorName.GEMINI_VISION)
            # Non-searchable PDFs still try PyMuPDF first for mixed/partial text.
            if not probe.is_searchable_pdf and ExtractorName.PYMUPDF not in chain:
                chain.insert(0, ExtractorName.PYMUPDF)
            return chain

        raise UnsupportedFileError(f"No extraction plan for kind={probe.kind}")

    def _gemini_available(self) -> bool:
        return bool(
            self._settings.gemini_vision_enabled and self._settings.gemini_api_key
        )
