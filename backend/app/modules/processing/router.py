from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies.auth import CurrentUser
from app.modules.processing.dependencies import get_document_worker, get_processing_service
from app.modules.processing.exceptions import ProcessingJobNotFoundError
from app.modules.processing.schemas import (
    ProcessingControlResponse,
    ProcessingJobResponse,
    ProcessingStatusResponse,
)
from app.modules.processing.service import ProcessingService
from app.workers.interface import DocumentWorker

router = APIRouter(prefix="/processing", tags=["processing"])


@router.get("/status", response_model=ProcessingStatusResponse)
async def get_processing_status(
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
) -> ProcessingStatusResponse:
    return await service.get_status(current_user)


@router.get("/jobs/{job_id}", response_model=ProcessingJobResponse)
async def get_processing_job(
    job_id: UUID,
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
) -> ProcessingJobResponse:
    try:
        return await service.get_job(current_user, job_id)
    except ProcessingJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        ) from exc


@router.post("/pause", response_model=ProcessingControlResponse)
async def pause_processing_globally(
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
) -> ProcessingControlResponse:
    return await service.pause_global(current_user)


@router.post("/resume", response_model=ProcessingControlResponse)
async def resume_processing_globally(
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
) -> ProcessingControlResponse:
    return await service.resume_global(current_user)


@router.post("/jobs/{job_id}/pause", response_model=ProcessingJobResponse)
async def pause_processing_job(
    job_id: UUID,
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
) -> ProcessingJobResponse:
    try:
        return await service.pause_job(current_user, job_id)
    except ProcessingJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        ) from exc


@router.post("/jobs/{job_id}/resume", response_model=ProcessingJobResponse)
async def resume_processing_job(
    job_id: UUID,
    current_user: CurrentUser,
    service: ProcessingService = Depends(get_processing_service),
    worker: DocumentWorker | None = Depends(get_document_worker),
) -> ProcessingJobResponse:
    try:
        response = await service.resume_job(current_user, job_id)
    except ProcessingJobNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Processing job not found",
        ) from exc

    if worker is not None:
        await worker.enqueue(response.document_id)

    return response
