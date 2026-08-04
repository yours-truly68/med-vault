from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings, get_settings
from app.core.database.session import Database


def get_database(request: Request) -> Database:
    database: Database = request.app.state.database
    return database


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    database = get_database(request)
    async for session in database.session():
        yield session


def get_app_settings() -> Settings:
    return get_settings()
