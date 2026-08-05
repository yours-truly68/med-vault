"""Storage factory for instantiating the configured StorageProvider."""

from __future__ import annotations

import logging
import threading

from app.core.config.settings import Settings, get_settings
from app.core.storage.base import StorageProvider
from app.core.storage.local_provider import LocalStorageProvider
from app.core.storage.s3_provider import S3StorageProvider

logger = logging.getLogger(__name__)

# Module-level singleton — created once at first call, reused for the lifetime
# of the process. A threading.Lock guards the double-checked locking so two
# concurrent requests can't both race to initialise.
_provider_instance: StorageProvider | None = None
_provider_lock = threading.Lock()


def get_storage_provider(settings: Settings | None = None) -> StorageProvider:
    """Return the process-wide singleton StorageProvider.

    If an explicit `settings` object is provided, a provider for that configuration
    is created and returned directly (useful for tests or custom settings overrides).
    Otherwise, the process-wide singleton is returned.
    """
    global _provider_instance

    if settings is not None:
        return _create_storage_provider(settings)

    # Fast path for global singleton when settings is None
    if _provider_instance is not None:
        return _provider_instance

    with _provider_lock:
        if _provider_instance is not None:
            return _provider_instance

        cfg = get_settings()
        _provider_instance = _create_storage_provider(cfg)
        return _provider_instance


def _create_storage_provider(cfg: Settings) -> StorageProvider:
    provider_name = (cfg.storage_provider or "minio").lower().strip()

    logger.info("Initializing StorageProvider: provider=%s", provider_name)

    if provider_name in ("minio", "s3", "r2", "b2", "spaces", "s3_compatible"):
        return S3StorageProvider(cfg)
    elif provider_name == "local":
        return LocalStorageProvider(cfg)
    else:
        logger.warning(
            "Unknown STORAGE_PROVIDER '%s'. Defaulting to S3StorageProvider.",
            provider_name,
        )
        return S3StorageProvider(cfg)


def reset_storage_provider() -> None:
    """Reset the singleton — useful in tests that need a fresh provider."""
    global _provider_instance
    with _provider_lock:
        _provider_instance = None
