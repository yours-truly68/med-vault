"""Storage abstraction package for MedVault."""

from app.core.storage.base import StorageMetadata, StorageObject, StorageProvider
from app.core.storage.factory import get_storage_provider

__all__ = [
    "StorageMetadata",
    "StorageObject",
    "StorageProvider",
    "get_storage_provider",
]
