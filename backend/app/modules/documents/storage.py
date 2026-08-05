"""Document storage wrapper delegating to the unified StorageProvider abstraction."""

from __future__ import annotations

import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config.settings import Settings
from app.core.storage import StorageObject, StorageProvider, get_storage_provider
from app.modules.documents.exceptions import FileTooLargeError, InvalidFileTypeError

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


@dataclass(frozen=True)
class SavedFile:
    storage_path: str  # object_key
    bucket: str
    file_size_bytes: int
    content_type: str
    checksum: str  # SHA-256 hex digest
    original_filename: str

    @property
    def object_key(self) -> str:
        return self.storage_path


class DocumentStorageManager:
    """High-level document storage manager utilizing configured StorageProvider abstraction."""

    def __init__(
        self,
        settings: Settings,
        provider: StorageProvider | None = None,
    ) -> None:
        self._settings = settings
        self._provider = provider or get_storage_provider(settings)
        self._max_bytes = settings.max_upload_size_mb * 1024 * 1024

    @property
    def provider(self) -> StorageProvider:
        return self._provider

    async def save(
        self,
        *,
        user_id: UUID,
        family_member_id: UUID,
        upload: UploadFile,
    ) -> SavedFile:
        original_filename = self._sanitize_filename(upload.filename)
        content_type = self._resolve_content_type(upload, original_filename)
        extension = self._validate_file(original_filename, content_type)

        object_key = f"documents/{user_id}/{family_member_id}/{uuid4()}{extension}"

        # Read file contents & validate size
        file_bytes = await upload.read()
        if len(file_bytes) == 0:
            raise InvalidFileTypeError("Uploaded file is empty")
        if len(file_bytes) > self._max_bytes:
            raise FileTooLargeError(
                f"File exceeds the {self._max_bytes // (1024 * 1024)} MB limit"
            )

        # Upload via provider-agnostic StorageProvider
        obj: StorageObject = self._provider.upload(
            object_key,
            file_bytes,
            content_type=content_type,
            metadata={
                "original_filename": original_filename,
                "user_id": str(user_id),
                "family_member_id": str(family_member_id),
            },
        )

        return SavedFile(
            storage_path=obj.object_key,
            bucket=obj.bucket,
            file_size_bytes=obj.size_bytes,
            content_type=obj.content_type,
            checksum=obj.checksum,
            original_filename=original_filename,
        )

    def delete(self, object_key: str) -> None:
        self._provider.delete(object_key)

    def resolve_path(self, storage_path: str) -> Path:
        if hasattr(self._provider, "_resolve_path"):
            return getattr(self._provider, "_resolve_path")(storage_path)
        import tempfile
        ext = Path(storage_path).suffix or ".pdf"
        tmp_path = Path(tempfile.NamedTemporaryFile(suffix=ext, delete=False).name)
        return self._provider.download_file(storage_path, tmp_path)

    def download_bytes(self, object_key: str) -> bytes:
        return self._provider.download(object_key)

    def download_to_temp_file(self, object_key: str, temp_path: Path) -> Path:
        return self._provider.download_file(object_key, temp_path)

    def generate_presigned_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        return self._provider.generate_presigned_url(
            object_key,
            expires_in=expires_in,
            filename=filename,
        )

    def _sanitize_filename(self, filename: str | None) -> str:
        if not filename:
            raise InvalidFileTypeError("Filename is required")

        safe_name = Path(filename).name.strip()
        if not safe_name or safe_name in {".", ".."}:
            raise InvalidFileTypeError("Invalid filename")

        return safe_name

    def _resolve_content_type(self, upload: UploadFile, filename: str) -> str:
        content_type = (upload.content_type or "").split(";", 1)[0].strip().lower()
        if content_type in ALLOWED_CONTENT_TYPES:
            return content_type

        guessed_type, _ = mimetypes.guess_type(filename)
        if guessed_type and guessed_type in ALLOWED_CONTENT_TYPES:
            return guessed_type

        raise InvalidFileTypeError("Only PDF, JPG, JPEG, and PNG files are allowed")

    def _validate_file(self, filename: str, content_type: str) -> str:
        extension = Path(filename).suffix.lower()
        if extension not in {".pdf", ".jpg", ".jpeg", ".png"}:
            raise InvalidFileTypeError("Only PDF, JPG, JPEG, and PNG files are allowed")

        expected_extension = ALLOWED_CONTENT_TYPES[content_type]
        if extension == ".jpeg" and content_type == "image/jpeg":
            return expected_extension

        if extension != expected_extension:
            raise InvalidFileTypeError("File extension does not match content type")

        return expected_extension


# For backwards compatibility with previous imports:
LocalDocumentStorage = DocumentStorageManager
