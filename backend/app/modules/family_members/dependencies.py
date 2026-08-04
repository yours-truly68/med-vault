from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.database import get_db
from app.modules.family_members.service import FamilyMemberService


async def get_family_member_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FamilyMemberService:
    return FamilyMemberService(session=db)


FamilyMemberServiceDep = Annotated[FamilyMemberService, Depends(get_family_member_service)]
