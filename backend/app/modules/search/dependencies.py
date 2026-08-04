from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.dependencies.database import get_app_settings, get_db
from app.modules.search.service import SearchService


async def get_search_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> SearchService:
    return SearchService(session=db, settings=settings)


SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
