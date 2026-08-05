from typing import Annotated
from uuid import UUID
from datetime import date

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.database import get_db
from app.modules.family_members.exceptions import FamilyMemberNotFoundError
from app.modules.family_members.repository import FamilyMemberRepository
from app.modules.health.repository import HealthRepository
from app.modules.health.service import HealthService


async def get_health_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HealthService:
    return HealthService(HealthRepository(db), FamilyMemberRepository(db))


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]
