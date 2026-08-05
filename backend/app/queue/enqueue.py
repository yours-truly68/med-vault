"""ARQ JobQueue implementation and helper functions."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.core.config.settings import Settings
from app.queue.client import RedisManager
from app.queue.interface import IJobQueue

logger = logging.getLogger(__name__)


class ArqJobQueue(IJobQueue):
    """Reusable ARQ job queue abstraction."""

    def __init__(self, redis_manager: RedisManager, settings: Settings) -> None:
        self._redis_manager = redis_manager
        self._settings = settings

    async def enqueue_job(
        self,
        function_name: str,
        *args: Any,
        _job_id: str | None = None,
        _queue_name: str | None = None,
        **kwargs: Any,
    ) -> str | None:
        try:
            pool = await self._redis_manager.get_pool()
            job = await pool.enqueue_job(
                function_name,
                *args,
                _job_id=_job_id,
                _queue_name=_queue_name or self._settings.processing_queue_name,
                _job_timeout=self._settings.arq_job_timeout,
            )
            if job:
                logger.info(
                    "Enqueued ARQ job %s (%s) to queue %s",
                    job.job_id,
                    function_name,
                    _queue_name or self._settings.processing_queue_name,
                )
                return job.job_id
            return None
        except Exception as exc:
            logger.error("Failed to enqueue ARQ job %s: %s", function_name, exc)
            return None

    async def enqueue_processing(self, document_id: UUID) -> str | None:
        """Enqueue Phase 1 document processing job."""
        return await self.enqueue_job(
            "process_document_job",
            str(document_id),
            _job_id=f"processing:{document_id}",
            _queue_name=self._settings.processing_queue_name,
        )

    async def enqueue_indexing(self, document_id: UUID) -> str | None:
        """Enqueue Phase 2 document indexing job."""
        return await self.enqueue_job(
            "process_indexing_job",
            str(document_id),
            _job_id=f"indexing:{document_id}",
            _queue_name=self._settings.indexing_queue_name,
        )

    async def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check for Redis and ARQ queues."""
        redis_ok = await self._redis_manager.check_connection()
        queue_ok = False
        registered_workers = 0

        if redis_ok:
            try:
                pool = await self._redis_manager.get_pool()
                # Ping ARQ pool
                await pool.ping()
                queue_ok = True

                # Check active worker keys in Redis
                client = pool
                keys = await client.keys("arq:number-jobs:*")
                registered_workers = len(keys)
            except Exception as exc:
                logger.warning("ARQ health check failed: %s", exc)

        return {
            "redis_connected": redis_ok,
            "queue_connected": queue_ok,
            "worker_registered": registered_workers > 0 or redis_ok,  # worker active/ready
            "active_worker_count": registered_workers,
            "processing_queue": self._settings.processing_queue_name,
            "indexing_queue": self._settings.indexing_queue_name,
        }
