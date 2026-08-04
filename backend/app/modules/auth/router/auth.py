from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status

from app.core.config.settings import Settings
from app.core.dependencies.auth import CurrentUser, get_auth_service
from app.core.dependencies.database import get_app_settings
from app.core.exceptions import UnauthorizedError
from app.modules.auth.router.cookies import (
    build_auth_response,
    clear_refresh_token_cookie,
    set_refresh_token_cookie,
)
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionUser,
)
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserDetail

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthResponse:
    tokens = await auth_service.register(payload)
    set_refresh_token_cookie(response, tokens.refresh_token, settings)
    return build_auth_response(tokens)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> AuthResponse:
    tokens = await auth_service.login(payload)
    set_refresh_token_cookie(response, tokens.refresh_token, settings)
    return build_auth_response(tokens)


@router.post("/refresh", response_model=AuthResponse)
async def refresh_session(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> AuthResponse:
    if not refresh_token:
        raise UnauthorizedError("Refresh token is missing")

    tokens = await auth_service.refresh(refresh_token)
    set_refresh_token_cookie(response, tokens.refresh_token, settings)
    return build_auth_response(tokens)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_app_settings)],
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> MessageResponse:
    await auth_service.logout(refresh_token)
    clear_refresh_token_cookie(response, settings)
    return MessageResponse(message="Logged out successfully")


@router.get("/me", response_model=SessionUser)
async def get_current_user_profile(current_user: CurrentUser) -> SessionUser:
    return SessionUser(user=UserDetail.model_validate(current_user))
