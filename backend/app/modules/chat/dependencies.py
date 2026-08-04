from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.dependencies.database import get_app_settings, get_db
from app.modules.chat.service import ChatService


async def get_chat_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> ChatService:
    return ChatService(session=db, settings=settings)


ChatServiceDep = Annotated[ChatService, Depends(get_chat_service)]
