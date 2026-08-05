import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config.settings import Settings, get_settings
from app.core.database import models as _models  # noqa: F401
from app.core.database.session import Database
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.ai.validation import ConfigurationError, validate_application_configuration

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    try:
        validate_application_configuration(settings)
    except ConfigurationError as exc:
        logger.error("Configuration validation failed: %s", exc)
        raise

    database = Database(settings)
    app.state.database = database

    document_worker = InProcessDocumentWorker(
        database,
        settings,
        concurrency=settings.document_worker_concurrency,
    )
    await document_worker.start()
    app.state.document_worker = document_worker

    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment)

    yield

    await document_worker.stop()
    await database.dispose()
    logger.info("Shutdown complete")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.state.settings = settings

    register_exception_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(api_router)

    return app


app = create_app()
