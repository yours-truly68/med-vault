from typing import Annotated
from uuid import UUID
from datetime import date

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies.database import get_db
from app.modules.timeline.repository import TimelineRepository
from app.modules.timeline.service import TimelineService


async def get_timeline_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TimelineService:
    return TimelineService(TimelineRepository(db))


TimelineServiceDep = Annotated[TimelineService, Depends(get_timeline_service)]
