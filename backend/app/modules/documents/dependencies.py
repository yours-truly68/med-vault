from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.dependencies.database import get_app_settings, get_db
from app.modules.documents.service import DocumentService
from app.workers.interface import DocumentWorker


def get_document_worker(request: Request) -> DocumentWorker | None:
    return getattr(request.app.state, "document_worker", None)


async def get_document_service(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> DocumentService:
    worker: DocumentWorker | None = get_document_worker(request)
    job_queue = getattr(request.app.state, "job_queue", None)
    return DocumentService(session=db, settings=settings, worker=worker, job_queue=job_queue)


DocumentServiceDep = Annotated[DocumentService, Depends(get_document_service)]
