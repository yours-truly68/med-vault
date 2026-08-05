"""Local filesystem storage provider implementation of StorageProvider protocol."""

from __future__ import annotations

import hashlib
import io
import mimetypes
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from app.core.config.settings import Settings
from app.core.storage.base import StorageMetadata, StorageObject, StorageProvider


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider (useful for offline testing or legacy local fallback)."""

    def __init__(self, settings: Settings) -> None:
        self._root = Path(settings.upload_dir).resolve()
        self._bucket = "local-filesystem"

    def upload(
        self,
        object_key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StorageObject:
        destination = (self._root / object_key).resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(data, bytes):
            raw_bytes = data
        else:
            raw_bytes = data.read()

        hasher = hashlib.sha256(raw_bytes)
        checksum = hasher.hexdigest()

        with destination.open("wb") as f:
            f.write(raw_bytes)

        mime = content_type or mimetypes.guess_type(object_key)[0] or "application/octet-stream"

        return StorageObject(
            object_key=object_key,
            bucket=self._bucket,
            size_bytes=len(raw_bytes),
            content_type=mime,
            checksum=checksum,
            uploaded_at=datetime.now(timezone.utc),
        )

    def download(self, object_key: str) -> bytes:
        file_path = self._resolve_path(object_key)
        return file_path.read_bytes()

    def download_file(self, object_key: str, destination_path: Path) -> Path:
        file_path = self._resolve_path(object_key)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination_path)
        return destination_path

    def delete(self, object_key: str) -> None:
        try:
            file_path = self._resolve_path(object_key)
            if file_path.is_file():
                file_path.unlink()
        except FileNotFoundError:
            pass

    def exists(self, object_key: str) -> bool:
        try:
            file_path = self._resolve_path(object_key)
            return file_path.is_file()
        except FileNotFoundError:
            return False

    def stat(self, object_key: str) -> StorageMetadata:
        file_path = self._resolve_path(object_key)
        stat_res = file_path.stat()
        checksum = hashlib.sha256(file_path.read_bytes()).hexdigest()
        mime = mimetypes.guess_type(object_key)[0] or "application/octet-stream"

        return StorageMetadata(
            object_key=object_key,
            bucket=self._bucket,
            size_bytes=stat_res.st_size,
            content_type=mime,
            checksum=checksum,
            last_modified=datetime.fromtimestamp(stat_res.st_mtime, tz=timezone.utc),
        )

    def generate_presigned_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        # Local provider returns a proxy path endpoint
        return f"/api/v1/documents/file/{object_key}"

    def copy(self, source_key: str, destination_key: str) -> None:
        src = self._resolve_path(source_key)
        dst = (self._root / destination_key).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def move(self, source_key: str, destination_key: str) -> None:
        src = self._resolve_path(source_key)
        dst = (self._root / destination_key).resolve()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    def _resolve_path(self, object_key: str) -> Path:
        file_path = (self._root / object_key).resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"Object key not found in storage: {object_key}")
        if self._root not in file_path.parents and file_path != self._root:
            raise ValueError("Invalid object key path")
        return file_path
