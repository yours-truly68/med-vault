"""Abstract interface for ARQ job queue."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class IJobQueue(ABC):
    """Abstract job queue interface for enqueuing async tasks."""

    @abstractmethod
    async def enqueue_job(
        self,
        function_name: str,
        *args: Any,
        _job_id: str | None = None,
        _queue_name: str | None = None,
        **kwargs: Any,
    ) -> str | None:
        """Enqueue a job to the queue."""
        pass

    @abstractmethod
    async def enqueue_processing(self, document_id: UUID) -> str | None:
        """Enqueue Phase 1 document processing."""
        pass

    @abstractmethod
    async def enqueue_indexing(self, document_id: UUID) -> str | None:
        """Enqueue Phase 2 document indexing."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Perform a health check on Redis, queue connection, and worker status."""
        pass
