from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.family_members.models import FamilyMember


class FamilyMemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_user_id(self, user_id: UUID) -> list[FamilyMember]:
        result = await self._session.execute(
            select(FamilyMember)
            .where(FamilyMember.user_id == user_id)
            .order_by(FamilyMember.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_by_user_id(self, user_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(FamilyMember)
            .where(FamilyMember.user_id == user_id)
        )
        return int(result.scalar_one())

    async def get_by_id_and_user_id(
        self,
        member_id: UUID,
        user_id: UUID,
    ) -> FamilyMember | None:
        result = await self._session.execute(
            select(FamilyMember).where(
                FamilyMember.id == member_id,
                FamilyMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_user_id_and_name(
        self,
        user_id: UUID,
        name: str,
        *,
        exclude_id: UUID | None = None,
    ) -> FamilyMember | None:
        query = select(FamilyMember).where(
            FamilyMember.user_id == user_id,
            FamilyMember.name == name,
        )
        if exclude_id is not None:
            query = query.where(FamilyMember.id != exclude_id)

        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        relationship_type: str,
        date_of_birth: date | None,
    ) -> FamilyMember:
        member = FamilyMember(
            user_id=user_id,
            name=name,
            relationship_type=relationship_type,
            date_of_birth=date_of_birth,
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def update(self, member: FamilyMember) -> FamilyMember:
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def delete(self, member: FamilyMember) -> None:
        await self._session.delete(member)
        await self._session.flush()
