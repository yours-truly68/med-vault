from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Form, Query, UploadFile, status

from app.core.database.enums import DocumentStatus, DocumentType
from app.core.dependencies.auth import CurrentUser
from app.modules.auth.schemas import MessageResponse
from app.modules.documents.dependencies import DocumentServiceDep
from app.modules.documents.schemas import (
    DocumentListResponse,
    DocumentUploadListResponse,
    DocumentUploadResponse,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=DocumentUploadListResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_documents(
    family_member_id: Annotated[UUID, Form()],
    files: Annotated[list[UploadFile], File()],
    current_user: CurrentUser,
    service: DocumentServiceDep,
) -> DocumentUploadListResponse:
    return await service.upload_documents(current_user, family_member_id, files)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    current_user: CurrentUser,
    service: DocumentServiceDep,
    family_member_id: Annotated[UUID | None, Query()] = None,
    document_type: Annotated[DocumentType | None, Query()] = None,
    status_filter: Annotated[
        DocumentStatus | None,
        Query(alias="status"),
    ] = None,
) -> DocumentListResponse:
    return await service.list_documents(
        current_user,
        family_member_id=family_member_id,
        document_type=document_type,
        status=status_filter,
    )


from fastapi.responses import FileResponse

@router.get("/{document_id}", response_model=DocumentUploadResponse)
async def get_document(
    document_id: UUID,
    current_user: CurrentUser,
    service: DocumentServiceDep,
) -> DocumentUploadResponse:
    return await service.get_document(current_user, document_id)


@router.get("/{document_id}/file")
async def get_document_file(
    document_id: UUID,
    current_user: CurrentUser,
    service: DocumentServiceDep,
) -> FileResponse:
    file_path, content_type, filename = await service.get_document_file(current_user, document_id)
    return FileResponse(
        path=file_path,
        media_type=content_type,
        filename=filename,
    )


@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: UUID,
    current_user: CurrentUser,
    service: DocumentServiceDep,
) -> MessageResponse:
    return await service.delete_document(current_user, document_id)


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reprocess_document(
    document_id: UUID,
    current_user: CurrentUser,
    service: DocumentServiceDep,
) -> DocumentUploadResponse:
    return await service.reprocess_document(current_user, document_id)
