from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.family_members.exceptions import (
    DuplicateFamilyMemberNameError,
    FamilyMemberNotFoundError,
)
from app.modules.family_members.models import FamilyMember
from app.modules.family_members.repository import FamilyMemberRepository
from app.modules.family_members.schemas import (
    FamilyMemberCreate,
    FamilyMemberListResponse,
    FamilyMemberResponse,
    FamilyMemberUpdate,
)
from app.modules.users.models.models import User


class FamilyMemberService:
    def __init__(
        self,
        session: AsyncSession,
        repository: FamilyMemberRepository | None = None,
    ) -> None:
        self._session = session
        self._repository = repository or FamilyMemberRepository(session)

    async def list_members(self, user: User) -> FamilyMemberListResponse:
        members = await self._repository.list_by_user_id(user.id)
        return FamilyMemberListResponse(
            items=[FamilyMemberResponse.model_validate(member) for member in members],
            total=len(members),
        )

    async def create_member(self, user: User, payload: FamilyMemberCreate) -> FamilyMemberResponse:
        await self._ensure_unique_name(user.id, payload.name)
        member = await self._repository.create(
            user_id=user.id,
            name=payload.name,
            relationship_type=payload.relationship_type.value,
            date_of_birth=payload.date_of_birth,
        )
        return FamilyMemberResponse.model_validate(member)

    async def update_member(
        self,
        user: User,
        member_id: UUID,
        payload: FamilyMemberUpdate,
    ) -> FamilyMemberResponse:
        member = await self._get_owned_member(user.id, member_id)

        if payload.name is not None and payload.name != member.name:
            await self._ensure_unique_name(user.id, payload.name, exclude_id=member.id)
            member.name = payload.name

        if payload.relationship_type is not None:
            member.relationship_type = payload.relationship_type.value

        if "date_of_birth" in payload.model_fields_set:
            member.date_of_birth = payload.date_of_birth

        updated = await self._repository.update(member)
        return FamilyMemberResponse.model_validate(updated)

    async def delete_member(self, user: User, member_id: UUID) -> None:
        member = await self._get_owned_member(user.id, member_id)
        await self._repository.delete(member)

    async def _get_owned_member(self, user_id: UUID, member_id: UUID) -> FamilyMember:
        member = await self._repository.get_by_id_and_user_id(member_id, user_id)
        if member is None:
            raise FamilyMemberNotFoundError()
        return member

    async def _ensure_unique_name(
        self,
        user_id: UUID,
        name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> None:
        existing = await self._repository.get_by_user_id_and_name(
            user_id,
            name,
            exclude_id=exclude_id,
        )
        if existing is not None:
            raise DuplicateFamilyMemberNameError()
