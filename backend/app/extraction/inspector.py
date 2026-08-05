"""Document inspector — probes files without performing OCR."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import filetype
import pymupdf
from PIL import Image

from app.core.config.settings import Settings
from app.extraction.cache import ExtractionCache
from app.extraction.exceptions import CorruptFileError, UnsupportedFileError
from app.extraction.models import FileKind, FileProbe

logger = logging.getLogger(__name__)

PDF_MIMES = frozenset({"application/pdf"})
IMAGE_MIMES = frozenset({"image/jpeg", "image/png", "image/jpg"})
MIME_BY_EXT = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class FileInspector:
    def __init__(self, settings: Settings) -> None:
        self._min_native_chars = settings.ocr_min_native_text_chars

    async def inspect(
        self,
        path: Path,
        *,
        declared_content_type: str | None = None,
    ) -> FileProbe:
        return await asyncio.to_thread(
            self._inspect_sync,
            path,
            declared_content_type,
        )

    def _inspect_sync(
        self,
        path: Path,
        declared_content_type: str | None,
    ) -> FileProbe:
        if not path.is_file():
            raise UnsupportedFileError(f"File not found: {path}")

        size_bytes = path.stat().st_size
        if size_bytes == 0:
            raise CorruptFileError("Uploaded file is empty")

        file_sha256 = ExtractionCache.hash_file(path)
        extension = path.suffix.lower() or None
        mime_type = self._detect_mime(path, declared_content_type, extension)
        kind = self._kind_from_mime(mime_type)

        if kind == FileKind.UNKNOWN:
            raise UnsupportedFileError(f"Unsupported content type: {mime_type}")

        page_count_hint: int | None = None
        is_searchable_pdf: bool | None = None
        width: int | None = None
        height: int | None = None
        pdf_metadata: dict[str, str] = {}
        estimated_ocr_required = False

        if kind == FileKind.PDF:
            page_count_hint, is_searchable_pdf, pdf_metadata = self._probe_pdf(path)
            estimated_ocr_required = not bool(is_searchable_pdf)
        elif kind == FileKind.IMAGE:
            page_count_hint = 1
            width, height = self._probe_image(path)
            estimated_ocr_required = True

        return FileProbe(
            path=path,
            kind=kind,
            mime_type=mime_type,
            size_bytes=size_bytes,
            file_sha256=file_sha256,
            page_count_hint=page_count_hint,
            is_searchable_pdf=is_searchable_pdf,
            declared_content_type=declared_content_type,
            width=width,
            height=height,
            extension=extension,
            pdf_metadata=pdf_metadata,
            estimated_ocr_required=estimated_ocr_required,
        )

    def _detect_mime(
        self,
        path: Path,
        declared: str | None,
        extension: str | None,
    ) -> str:
        guessed = filetype.guess(str(path))
        if guessed is not None:
            return guessed.mime

        if declared:
            normalized = declared.split(";", 1)[0].strip().lower()
            if normalized in PDF_MIMES | IMAGE_MIMES or normalized == "image/jpg":
                return "image/jpeg" if normalized == "image/jpg" else normalized

        if extension and extension in MIME_BY_EXT:
            return MIME_BY_EXT[extension]

        raise UnsupportedFileError(
            f"Unable to detect file type for {path.name}"
        )

    def _kind_from_mime(self, mime_type: str) -> FileKind:
        if mime_type in PDF_MIMES:
            return FileKind.PDF
        if mime_type in IMAGE_MIMES or mime_type == "image/jpg":
            return FileKind.IMAGE
        return FileKind.UNKNOWN

    def _probe_pdf(self, path: Path) -> tuple[int, bool, dict[str, str]]:
        try:
            with pymupdf.open(path) as document:
                if document.page_count == 0:
                    raise CorruptFileError("PDF has no pages")

                sample_pages = min(document.page_count, 5)
                total_chars = 0
                for index in range(sample_pages):
                    total_chars += len(document[index].get_text().strip())
                avg = total_chars / sample_pages
                searchable = avg >= self._min_native_chars

                meta_raw = document.metadata or {}
                metadata = {
                    str(key): str(value)
                    for key, value in meta_raw.items()
                    if value
                }
                return document.page_count, searchable, metadata
        except CorruptFileError:
            raise
        except Exception as exc:
            raise CorruptFileError(f"Failed to inspect PDF: {exc}") from exc

    def _probe_image(self, path: Path) -> tuple[int | None, int | None]:
        try:
            with Image.open(path) as image:
                return image.width, image.height
        except Exception as exc:
            raise CorruptFileError(f"Failed to inspect image: {exc}") from exc
