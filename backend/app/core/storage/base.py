"""Base interface and data structures for provider-agnostic object storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO, Iterator


@dataclass(frozen=True)
class StorageObject:
    """Represents a stored object and its attributes."""

    object_key: str
    bucket: str
    size_bytes: int
    content_type: str
    checksum: str  # SHA-256 hex digest
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class StorageMetadata:
    """Represents metadata returned by stat()."""

    object_key: str
    bucket: str
    size_bytes: int
    content_type: str
    checksum: str | None = None
    etag: str | None = None
    last_modified: datetime | None = None


class StorageProvider(ABC):
    """Abstract storage provider protocol.

    Application components MUST interact exclusively with this abstraction,
    never directly touching local paths or provider-specific SDKs.
    """

    @abstractmethod
    def upload(
        self,
        object_key: str,
        data: bytes | BinaryIO,
        content_type: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> StorageObject:
        """Upload raw bytes or file stream to storage and return object attributes."""

    @abstractmethod
    def download(self, object_key: str) -> bytes:
        """Download raw object bytes into memory."""

    @abstractmethod
    def download_file(self, object_key: str, destination_path: Path) -> Path:
        """Download object directly to a local file path (e.g. temporary OCR file)."""

    @abstractmethod
    def delete(self, object_key: str) -> None:
        """Delete an object from storage."""

    @abstractmethod
    def exists(self, object_key: str) -> bool:
        """Check if an object key exists."""

    @abstractmethod
    def stat(self, object_key: str) -> StorageMetadata:
        """Get object metadata without downloading object content."""

    @abstractmethod
    def generate_presigned_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        filename: str | None = None,
    ) -> str:
        """Generate a secure presigned GET URL for temporary direct browser access."""

    @abstractmethod
    def copy(self, source_key: str, destination_key: str) -> None:
        """Copy an object from one key location to another within storage."""

    @abstractmethod
    def move(self, source_key: str, destination_key: str) -> None:
        """Move an object from source_key to destination_key."""
