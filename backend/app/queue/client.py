"""Redis connection pool management for ARQ."""

from __future__ import annotations

import logging
from typing import Any

from arq.connections import ArqRedis, RedisSettings, create_pool
from redis.asyncio import Redis

from app.core.config.settings import Settings

logger = logging.getLogger(__name__)


def get_redis_settings(settings: Settings) -> RedisSettings:
    """Construct ARQ RedisSettings from application configuration."""
    return RedisSettings(
        host=settings.redis_host,
        port=settings.redis_port,
        database=settings.redis_db,
    )


class RedisManager:
    """Manages Redis connection pool and raw Redis client for health checks."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pool: ArqRedis | None = None
        self._redis_settings = get_redis_settings(settings)

    async def get_pool(self) -> ArqRedis:
        """Get or create the ARQ Redis connection pool."""
        if self._pool is None:
            logger.info(
                "Connecting to Redis at %s:%s (db=%s)",
                self._redis_settings.host,
                self._redis_settings.port,
                self._redis_settings.database,
            )
            self._pool = await create_pool(self._redis_settings)
        return self._pool

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            logger.info("Closing Redis connection pool")
            await self._pool.close()
            self._pool = None

    async def check_connection(self) -> bool:
        """Ping Redis server to verify connectivity."""
        try:
            client = Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                socket_timeout=3.0,
            )
            await client.ping()
            await client.aclose()
            return True
        except Exception as exc:
            logger.warning("Redis ping failed: %s", exc)
            return False
