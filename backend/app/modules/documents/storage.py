import mimetypes
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile

from app.core.config.settings import Settings
from app.modules.documents.exceptions import FileTooLargeError, InvalidFileTypeError

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
}
EXTENSION_BY_CONTENT_TYPE = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}


@dataclass(frozen=True)
class SavedFile:
    storage_path: str
    file_size_bytes: int
    content_type: str
    original_filename: str


class LocalDocumentStorage:
    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.upload_dir).resolve()
        self._max_bytes = settings.max_upload_size_mb * 1024 * 1024

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

        destination_dir = self._root / str(user_id) / str(family_member_id)
        destination_dir.mkdir(parents=True, exist_ok=True)

        stored_name = f"{uuid4()}{extension}"
        absolute_path = destination_dir / stored_name
        relative_path = f"{user_id}/{family_member_id}/{stored_name}"

        file_size = await self._write_file(upload, absolute_path)

        return SavedFile(
            storage_path=relative_path,
            file_size_bytes=file_size,
            content_type=content_type,
            original_filename=original_filename,
        )

    def delete(self, storage_path: str) -> None:
        file_path = self._root / storage_path
        if file_path.is_file():
            file_path.unlink()

    def resolve_path(self, storage_path: str) -> Path:
        file_path = (self._root / storage_path).resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"Stored file not found: {storage_path}")
        if self._root not in file_path.parents:
            raise ValueError("Invalid storage path")
        return file_path

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
        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidFileTypeError("Only PDF, JPG, JPEG, and PNG files are allowed")

        expected_extension = EXTENSION_BY_CONTENT_TYPE[content_type]
        if extension == ".jpeg" and content_type == "image/jpeg":
            return expected_extension

        if extension != expected_extension:
            raise InvalidFileTypeError("File extension does not match content type")

        return expected_extension

    async def _write_file(self, upload: UploadFile, destination: Path) -> int:
        size = 0
        chunk_size = 1024 * 1024

        try:
            with destination.open("wb") as output:
                while True:
                    chunk = await upload.read(chunk_size)
                    if not chunk:
                        break

                    size += len(chunk)
                    if size > self._max_bytes:
                        raise FileTooLargeError(
                            f"File exceeds the {self._max_bytes // (1024 * 1024)} MB limit"
                        )

                    output.write(chunk)
        except Exception:
            if destination.exists():
                destination.unlink()
            raise

        if size == 0:
            if destination.exists():
                destination.unlink()
            raise InvalidFileTypeError("Uploaded file is empty")

        return size
