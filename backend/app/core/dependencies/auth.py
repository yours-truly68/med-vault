from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.dependencies.database import get_app_settings, get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.modules.auth.service import AuthService
from app.modules.users.models.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_auth_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthService:
    return AuthService(session=db, settings=settings)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> User:
    if credentials is None:
        raise UnauthorizedError("Not authenticated")

    payload = decode_access_token(credentials.credentials, settings)
    user_id = UUID(str(payload["sub"]))
    return await auth_service.get_user_by_id(user_id)


CurrentUser = Annotated[User, Depends(get_current_user)]
