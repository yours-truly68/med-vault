from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.dependencies.database import get_app_settings, get_database, get_db
from app.core.database.session import Database
from app.modules.processing.service import ProcessingService
from app.workers.interface import DocumentWorker


def get_document_worker(request: Request) -> DocumentWorker | None:
    return getattr(request.app.state, "document_worker", None)


def get_processing_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    database: Annotated[Database, Depends(get_database)],
) -> ProcessingService:
    return ProcessingService(session=session, settings=settings, database=database)
