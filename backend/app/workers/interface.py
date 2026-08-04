"""Background worker interface for document processing."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class DocumentWorker(Protocol):
    async def enqueue(self, document_id: UUID) -> None:
        """Schedule a document for background processing."""
        ...

    async def start(self) -> None:
        """Start the worker (e.g. consumer loop)."""
        ...

    async def stop(self) -> None:
        """Gracefully stop the worker."""
        ...
