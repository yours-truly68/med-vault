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

    The provider is created once on the first call (which may involve a
    network round-trip to check / create the S3 bucket) and cached for all
    subsequent requests.  Calling this function on every HTTP request was the
    root cause of 6-10 s latency spikes caused by boto3 TCP-connect timeouts
    to MinIO when the service is not available.

    Changing providers (MinIO -> AWS S3 -> Cloudflare R2 -> DigitalOcean
    Spaces -> Backblaze B2) requires ONLY environment variable updates.
    """
    global _provider_instance

    # Fast path — no lock needed once the singleton is set.
    if _provider_instance is not None:
        return _provider_instance

    with _provider_lock:
        # Double-checked locking: another thread may have initialised while
        # we were waiting for the lock.
        if _provider_instance is not None:
            return _provider_instance

        cfg = settings or get_settings()
        provider_name = (cfg.storage_provider or "minio").lower().strip()

        logger.info("Initializing StorageProvider singleton: provider=%s", provider_name)

        if provider_name in ("minio", "s3", "r2", "b2", "spaces", "s3_compatible"):
            _provider_instance = S3StorageProvider(cfg)
        elif provider_name == "local":
            _provider_instance = LocalStorageProvider(cfg)
        else:
            logger.warning(
                "Unknown STORAGE_PROVIDER '%s'. Defaulting to S3StorageProvider.",
                provider_name,
            )
            _provider_instance = S3StorageProvider(cfg)

        return _provider_instance


def reset_storage_provider() -> None:
    """Reset the singleton — useful in tests that need a fresh provider."""
    global _provider_instance
    with _provider_lock:
        _provider_instance = None
