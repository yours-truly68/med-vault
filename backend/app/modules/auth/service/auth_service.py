from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import Settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.users.models.models import User
from app.modules.users.repository import UserRepository


@dataclass(frozen=True)
class AuthTokens:
    user: User
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        user_repository: UserRepository | None = None,
        refresh_token_repository: RefreshTokenRepository | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._users = user_repository or UserRepository(session)
        self._refresh_tokens = refresh_token_repository or RefreshTokenRepository(session)

    async def register(self, payload: RegisterRequest) -> AuthTokens:
        existing_user = await self._users.get_by_email(payload.email)
        if existing_user is not None:
            raise ConflictError("An account with this email already exists")

        user = await self._users.create(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
        )
        return await self._issue_tokens(user)

    async def login(self, payload: LoginRequest) -> AuthTokens:
        user = await self._users.get_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise UnauthorizedError("Invalid email or password")

        return await self._issue_tokens(user)

    async def refresh(self, refresh_token: str) -> AuthTokens:
        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self._refresh_tokens.get_by_hash(token_hash)

        if stored_token is None or not stored_token.is_active:
            raise UnauthorizedError("Invalid refresh token")

        if stored_token.expires_at <= datetime.now(UTC):
            await self._refresh_tokens.revoke(stored_token)
            raise UnauthorizedError("Refresh token has expired")

        user = await self._users.get_by_id(stored_token.user_id)
        if user is None:
            raise UnauthorizedError("Invalid refresh token")

        await self._refresh_tokens.revoke(stored_token)
        return await self._issue_tokens(user)

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return

        token_hash = hash_refresh_token(refresh_token)
        stored_token = await self._refresh_tokens.get_by_hash(token_hash)
        if stored_token is not None and stored_token.is_active:
            await self._refresh_tokens.revoke(stored_token)

    async def get_user_by_id(self, user_id: UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise UnauthorizedError("User not found")
        return user

    async def _issue_tokens(self, user: User) -> AuthTokens:
        access_token, expires_in = create_access_token(
            user_id=user.id,
            settings=self._settings,
        )
        refresh_token = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(days=self._settings.refresh_token_expire_days)

        await self._refresh_tokens.create(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )

        return AuthTokens(
            user=user,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
