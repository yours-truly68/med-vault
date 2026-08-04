"""In-process asyncio worker for document processing."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.processing.processor import DocumentProcessor

logger = logging.getLogger(__name__)


class InProcessDocumentWorker:
    def __init__(
        self,
        processor: DocumentProcessor,
        *,
        concurrency: int = 2,
    ) -> None:
        self._processor = processor
        self._concurrency = max(1, concurrency)
        self._queue: asyncio.Queue[UUID] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(self._concurrency)
        self._consumer_task: asyncio.Task[None] | None = None
        self._running = False
        self._in_flight: set[asyncio.Task[None]] = set()

    async def enqueue(self, document_id: UUID) -> None:
        await self._queue.put(document_id)
        logger.debug("Enqueued document %s for processing", document_id)

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._consumer_task = asyncio.create_task(self._consume())
        logger.info(
            "In-process document worker started (concurrency=%s)",
            self._concurrency,
        )

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        if self._consumer_task is not None:
            self._consumer_task.cancel()
            try:
                await self._consumer_task
            except asyncio.CancelledError:
                pass
            self._consumer_task = None

        if self._in_flight:
            await asyncio.gather(*self._in_flight, return_exceptions=True)
            self._in_flight.clear()

        logger.info("In-process document worker stopped")

    async def _consume(self) -> None:
        while self._running:
            document_id = await self._queue.get()
            task = asyncio.create_task(self._run_job(document_id))
            self._in_flight.add(task)
            task.add_done_callback(self._in_flight.discard)
            task.add_done_callback(lambda _: self._queue.task_done())

    async def _run_job(self, document_id: UUID) -> None:
        async with self._semaphore:
            try:
                await self._processor.process(document_id)
            except Exception:
                logger.exception("Unhandled error processing document %s", document_id)
