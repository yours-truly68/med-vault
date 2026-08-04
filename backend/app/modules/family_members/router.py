from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, status

from app.core.dependencies.auth import CurrentUser
from app.modules.auth.schemas import MessageResponse
from app.modules.family_members.dependencies import FamilyMemberServiceDep
from app.modules.family_members.schemas import (
    FamilyMemberCreate,
    FamilyMemberListResponse,
    FamilyMemberResponse,
    FamilyMemberUpdate,
)

router = APIRouter(prefix="/family-members", tags=["family-members"])


@router.get("", response_model=FamilyMemberListResponse)
async def list_family_members(
    current_user: CurrentUser,
    service: FamilyMemberServiceDep,
) -> FamilyMemberListResponse:
    return await service.list_members(current_user)


@router.post("", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def create_family_member(
    payload: FamilyMemberCreate,
    current_user: CurrentUser,
    service: FamilyMemberServiceDep,
) -> FamilyMemberResponse:
    return await service.create_member(current_user, payload)


@router.patch("/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: UUID,
    payload: FamilyMemberUpdate,
    current_user: CurrentUser,
    service: FamilyMemberServiceDep,
) -> FamilyMemberResponse:
    return await service.update_member(current_user, member_id, payload)


@router.delete("/{member_id}", response_model=MessageResponse)
async def delete_family_member(
    member_id: UUID,
    current_user: CurrentUser,
    service: FamilyMemberServiceDep,
) -> MessageResponse:
    await service.delete_member(current_user, member_id)
    return MessageResponse(message="Family member deleted successfully")
