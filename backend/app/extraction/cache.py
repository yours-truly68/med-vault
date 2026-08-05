"""SHA256 content-addressed extraction cache."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from pathlib import Path

from app.extraction.models import ExtractionResult

logger = logging.getLogger(__name__)

CACHE_SCHEMA_VERSION = "v1"


class ExtractionCache:
    def __init__(
        self,
        cache_dir: Path,
        *,
        enabled: bool = True,
        ttl_seconds: int | None = None,
    ) -> None:
        self._dir = cache_dir
        self._enabled = enabled
        self._ttl = ttl_seconds
        if enabled:
            self._dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def hash_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest()

    async def get(self, file_sha256: str) -> ExtractionResult | None:
        if not self._enabled:
            return None
        return await asyncio.to_thread(self._get_sync, file_sha256)

    async def put(self, file_sha256: str, result: ExtractionResult) -> None:
        if not self._enabled:
            return
        await asyncio.to_thread(self._put_sync, file_sha256, result)

    def _cache_path(self, file_sha256: str) -> Path:
        return self._dir / f"{CACHE_SCHEMA_VERSION}-{file_sha256}.json"

    def _get_sync(self, file_sha256: str) -> ExtractionResult | None:
        path = self._cache_path(file_sha256)
        if not path.is_file():
            return None
        try:
            if self._ttl is not None:
                age = time.time() - path.stat().st_mtime
                if age > self._ttl:
                    path.unlink(missing_ok=True)
                    return None
            payload = json.loads(path.read_text(encoding="utf-8"))
            result = ExtractionResult.model_validate(payload)
            result.cache_hit = True
            return result
        except Exception as exc:
            logger.warning("Failed to read extraction cache %s: %s", path.name, exc)
            return None

    def _put_sync(self, file_sha256: str, result: ExtractionResult) -> None:
        path = self._cache_path(file_sha256)
        try:
            payload = result.model_dump(mode="json")
            payload["cache_hit"] = False
            path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to write extraction cache %s: %s", path.name, exc)
