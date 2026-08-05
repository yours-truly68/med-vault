"""In-process asyncio worker for document processing."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from app.core.config.settings import Settings
from app.core.database.enums import ProcessingStage
from app.core.database.session import Database
from app.modules.processing.repository import ProcessingRepository
from app.modules.processing.workers.process_document import process_document

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentJob:
    document_id: UUID
    embeddings_only: bool = False


class InProcessDocumentWorker:
    def __init__(
        self,
        database: Database,
        settings: Settings,
        *,
        concurrency: int = 2,
    ) -> None:
        self._database = database
        self._settings = settings
        self._concurrency = max(1, concurrency)
        self._queue: asyncio.Queue[DocumentJob] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(self._concurrency)
        self._consumer_task: asyncio.Task[None] | None = None
        self._retry_task: asyncio.Task[None] | None = None
        self._running = False
        self._in_flight: set[asyncio.Task[None]] = set()

    async def enqueue(
        self,
        document_id: UUID,
        *,
        embeddings_only: bool = False,
    ) -> None:
        await self._queue.put(DocumentJob(document_id=document_id, embeddings_only=embeddings_only))
        logger.debug(
            "Enqueued document %s for processing (embeddings_only=%s)",
            document_id,
            embeddings_only,
        )

    async def start(self) -> None:
        if self._running:
            return

        self._running = True
        self._consumer_task = asyncio.create_task(self._consume())
        self._retry_task = asyncio.create_task(self._retry_loop())
        logger.info(
            "In-process document worker started (concurrency=%s)",
            self._concurrency,
        )

    async def stop(self) -> None:
        if not self._running:
            return

        self._running = False
        for task in (self._consumer_task, self._retry_task):
            if task is not None:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._consumer_task = None
        self._retry_task = None

        if self._in_flight:
            await asyncio.gather(*self._in_flight, return_exceptions=True)
            self._in_flight.clear()

        logger.info("In-process document worker stopped")

    async def _consume(self) -> None:
        while self._running:
            job = await self._queue.get()
            task = asyncio.create_task(self._run_job(job))
            self._in_flight.add(task)
            task.add_done_callback(self._in_flight.discard)
            task.add_done_callback(lambda _: self._queue.task_done())

    async def _retry_loop(self) -> None:
        poll_seconds = max(5.0, self._settings.deferred_retry_poll_seconds)
        while self._running:
            try:
                await asyncio.sleep(poll_seconds)
                await self._process_deferred_retries()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Deferred retry loop failed")

    async def _process_deferred_retries(self) -> None:
        async with self._database.session_factory() as session:
            repo = ProcessingRepository(session)
            jobs = await repo.list_jobs_ready_for_retry(limit=20)
            deferred: list[DocumentJob] = []
            for job in jobs:
                await repo.requeue_job_for_retry(job.id)
                deferred.append(
                    DocumentJob(
                        document_id=job.document_id,
                        embeddings_only=job.stage == ProcessingStage.EMBEDDINGS.value,
                    )
                )
            await session.commit()

        for job in deferred:
            await self.enqueue(job.document_id, embeddings_only=job.embeddings_only)

    async def _run_job(self, job: DocumentJob) -> None:
        async with self._semaphore:
            try:
                await process_document(
                    job.document_id,
                    database=self._database,
                    settings=self._settings,
                    embeddings_only=job.embeddings_only,
                )
            except Exception:
                logger.exception("Unhandled error processing document %s", job.document_id)
