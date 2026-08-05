"""Extraction router — builds ordered strategy chains from configuration."""

from __future__ import annotations

from app.core.config.settings import Settings
from app.extraction.exceptions import UnsupportedFileError
from app.extraction.models import ExtractorName, FileKind, FileProbe


_EXTRACTOR_ALIASES: dict[str, ExtractorName] = {
    "pymupdf": ExtractorName.PYMUPDF,
    "docling": ExtractorName.DOCLING,
    "tesseract": ExtractorName.TESSERACT,
    "gemini": ExtractorName.GEMINI_VISION,
    "gemini_vision": ExtractorName.GEMINI_VISION,
}


class ExtractionRouter:
    """Decides extractor order from environment configuration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def plan(self, probe: FileProbe) -> list[ExtractorName]:
        if probe.kind == FileKind.IMAGE:
            return self._build_chain(
                primary=self._settings.image_extractor,
                secondary=None,
            )

        if probe.kind == FileKind.PDF:
            chain = self._build_chain(
                primary=self._settings.primary_pdf_extractor,
                secondary=self._settings.secondary_pdf_extractor,
            )
            # Non-searchable PDFs still attempt the primary extractor first when omitted.
            primary = self._resolve_extractor(self._settings.primary_pdf_extractor)
            if (
                not probe.is_searchable_pdf
                and primary is not None
                and primary not in chain
            ):
                chain.insert(0, primary)
            return chain

        raise UnsupportedFileError(f"No extraction plan for kind={probe.kind}")

    def _build_chain(
        self,
        *,
        primary: str | None,
        secondary: str | None,
    ) -> list[ExtractorName]:
        chain: list[ExtractorName] = []
        for configured in (primary, secondary, "tesseract"):
            name = self._resolve_extractor(configured)
            if name is None:
                continue
            if not self._is_enabled(name):
                continue
            if name not in chain:
                chain.append(name)
        return chain

    def _resolve_extractor(self, value: str | None) -> ExtractorName | None:
        if not value or not value.strip():
            return None
        normalized = value.strip().lower().replace("-", "_")
        return _EXTRACTOR_ALIASES.get(normalized)

    def _is_enabled(self, extractor: ExtractorName) -> bool:
        if extractor == ExtractorName.DOCLING:
            return self._settings.docling_enabled
        if extractor == ExtractorName.TESSERACT:
            return self._settings.tesseract_enabled
        if extractor == ExtractorName.GEMINI_VISION:
            return False
        return True
