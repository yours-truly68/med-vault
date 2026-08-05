"""ARQ Worker programmatic runner script for Processing and Indexing queues."""

from __future__ import annotations

import asyncio
import logging

from arq.worker import Worker

from app.workers.settings import (
    IndexingWorkerSettings,
    ProcessingWorkerSettings,
    redis_settings,
    shutdown,
    startup,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_all_workers() -> None:
    """Run ARQ Processing and Indexing workers concurrently."""
    logger.info("Starting ARQ Workers (Processing Queue + Indexing Queue)...")
    proc_worker = Worker(
        functions=ProcessingWorkerSettings.functions,
        redis_settings=redis_settings,
        queue_name=ProcessingWorkerSettings.queue_name,
        on_startup=startup,
        on_shutdown=shutdown,
        job_timeout=ProcessingWorkerSettings.job_timeout,
        max_tries=ProcessingWorkerSettings.max_retries,
    )
    idx_worker = Worker(
        functions=IndexingWorkerSettings.functions,
        redis_settings=redis_settings,
        queue_name=IndexingWorkerSettings.queue_name,
        on_startup=startup,
        on_shutdown=shutdown,
        job_timeout=IndexingWorkerSettings.job_timeout,
        max_tries=IndexingWorkerSettings.max_retries,
    )
    await asyncio.gather(proc_worker.async_run(), idx_worker.async_run())


def main() -> None:
    """Run the ARQ worker process programmatically."""
    asyncio.run(run_all_workers())


if __name__ == "__main__":
    main()
