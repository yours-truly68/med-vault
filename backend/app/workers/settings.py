"""ARQ Worker Settings and job function tasks for Processing and Indexing."""

from __future__ import annotations

import logging
import traceback
from typing import Any
from uuid import UUID

from arq.connections import RedisSettings

from app.core.config.settings import get_settings
from app.core.database.session import Database
from app.modules.indexing.workers.process_indexing import process_indexing
from app.modules.processing.instrumentation import (
    PipelineContext,
    log_pipeline_summary,
    log_stage_error,
    log_worker_exit,
    log_worker_pickup,
)
from app.modules.processing.workers.process_document import process_document
from app.queue.client import RedisManager, get_redis_settings
from app.queue.enqueue import ArqJobQueue
from app.queue.interface import IJobQueue

logger = logging.getLogger(__name__)

settings = get_settings()
redis_settings: RedisSettings = get_redis_settings(settings)


async def process_document_job(ctx: dict[str, Any], document_id: str, **kwargs: Any) -> str:
    """ARQ Worker task for Phase 1 document processing."""
    doc_uuid = UUID(document_id)
    database: Database = ctx["database"]
    app_settings = ctx["settings"]
    job_queue: IJobQueue | None = ctx.get("job_queue")

    pipeline_ctx = PipelineContext(
        document_id=doc_uuid,
        job_id=ctx.get("job_id", document_id),
        queue_name=app_settings.processing_queue_name,
        worker_name="ProcessingWorker",
    )
    log_worker_pickup(pipeline_ctx)

    try:
        await process_document(
            doc_uuid,
            database=database,
            settings=app_settings,
            job_queue=job_queue,
            pipeline_ctx=pipeline_ctx,
        )
        log_worker_exit(pipeline_ctx, success=True)
        log_pipeline_summary(pipeline_ctx)
        return f"processed:{document_id}"
    except Exception as exc:
        log_stage_error(pipeline_ctx, "worker_exit", pipeline_ctx._run_start, exc)
        log_worker_exit(pipeline_ctx, success=False, error=str(exc))
        log_pipeline_summary(pipeline_ctx)
        raise


async def process_indexing_job(ctx: dict[str, Any], document_id: str, **kwargs: Any) -> str:
    """ARQ Worker task for Phase 2 document indexing."""
    doc_uuid = UUID(document_id)
    database: Database = ctx["database"]
    app_settings = ctx["settings"]

    pipeline_ctx = PipelineContext(
        document_id=doc_uuid,
        job_id=ctx.get("job_id", document_id),
        queue_name=app_settings.indexing_queue_name,
        worker_name="IndexingWorker",
    )
    log_worker_pickup(pipeline_ctx)

    try:
        await process_indexing(
            doc_uuid,
            database=database,
            settings=app_settings,
            pipeline_ctx=pipeline_ctx,
        )
        log_worker_exit(pipeline_ctx, success=True)
        log_pipeline_summary(pipeline_ctx)
        return f"indexed:{document_id}"
    except Exception as exc:
        log_stage_error(pipeline_ctx, "worker_exit", pipeline_ctx._run_start, exc)
        log_worker_exit(pipeline_ctx, success=False, error=str(exc))
        log_pipeline_summary(pipeline_ctx)
        raise


async def startup(ctx: dict[str, Any]) -> None:
    """Worker startup hook initializing database connection and job queue."""
    from app.core.database import models as _models  # noqa: F401
    app_settings = get_settings()
    database = Database(app_settings)
    redis_manager = RedisManager(app_settings)
    job_queue = ArqJobQueue(redis_manager, app_settings)

    ctx["settings"] = app_settings
    ctx["database"] = database
    ctx["redis_manager"] = redis_manager
    ctx["job_queue"] = job_queue
    logger.info("ARQ Worker initialized database connection, ORM models, and JobQueue")


async def shutdown(ctx: dict[str, Any]) -> None:
    """Worker shutdown hook disposing database and Redis connections."""
    database: Database | None = ctx.get("database")
    if database is not None:
        await database.dispose()
    redis_manager: RedisManager | None = ctx.get("redis_manager")
    if redis_manager is not None:
        await redis_manager.close()
    logger.info("ARQ Worker shutdown complete")


class ProcessingWorkerSettings:
    """ARQ Worker configuration for Phase 1 Processing Queue."""

    functions = [process_document_job]
    redis_settings = redis_settings
    job_timeout = settings.arq_job_timeout
    max_retries = settings.arq_max_retries
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.processing_queue_name


class IndexingWorkerSettings:
    """ARQ Worker configuration for Phase 2 Indexing Queue."""

    functions = [process_indexing_job]
    redis_settings = redis_settings
    job_timeout = settings.arq_job_timeout
    max_retries = settings.arq_max_retries
    on_startup = startup
    on_shutdown = shutdown
    queue_name = settings.indexing_queue_name


# Default alias for single-worker compatibility
WorkerSettings = ProcessingWorkerSettings
