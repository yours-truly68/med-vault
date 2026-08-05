"""Storage factory for instantiating the configured StorageProvider."""

from __future__ import annotations

from functools import lru_cache
import logging

from app.core.config.settings import Settings, get_settings
from app.core.storage.base import StorageProvider
from app.core.storage.local_provider import LocalStorageProvider
from app.core.storage.s3_provider import S3StorageProvider

logger = logging.getLogger(__name__)


_provider_instance: StorageProvider | None = None


def get_storage_provider(settings: Settings | None = None) -> StorageProvider:
    """Return an instance of StorageProvider based on STORAGE_PROVIDER config.

    Changing providers (MinIO -> AWS S3 -> Cloudflare R2 -> DigitalOcean Spaces -> Backblaze B2)
    requires ONLY environment variable updates. Application code remains unchanged.
    """
    cfg = settings or get_settings()
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
