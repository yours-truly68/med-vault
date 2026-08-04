from fastapi import Response

from app.core.config.settings import Settings
from app.modules.auth.schemas import AuthResponse
from app.modules.auth.service import AuthTokens
from app.modules.users.schemas import UserPublic


def build_auth_response(tokens: AuthTokens) -> AuthResponse:
    return AuthResponse(
        user=UserPublic.model_validate(tokens.user),
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
    )


def set_refresh_token_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_token_cookie_name,
        value=token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=settings.refresh_token_cookie_path,
    )


def clear_refresh_token_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_token_cookie_name,
        path=settings.refresh_token_cookie_path,
    )
