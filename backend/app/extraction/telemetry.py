"""Structured telemetry for extraction runs."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from app.extraction.models import ExtractionResult, FallbackAttempt, FileKind

logger = logging.getLogger("medvault.extraction.telemetry")


class ExtractionTelemetry:
    def record(
        self,
        *,
        result: ExtractionResult | None = None,
        document_id: UUID | None = None,
        file_sha256: str = "",
        mime_type: str = "",
        file_kind: FileKind | str = FileKind.UNKNOWN,
        error: str | None = None,
        fallbacks: list[FallbackAttempt] | None = None,
    ) -> None:
        event: dict[str, Any] = {
            "event": "document_extraction",
            "document_id": str(document_id) if document_id else None,
            "file_sha256": file_sha256 or (result.file_sha256 if result else ""),
            "mime_type": mime_type,
            "file_kind": str(file_kind),
            "error": error,
        }

        if result is not None:
            event.update(
                {
                    "extractor_used": result.extractor,
                    "elapsed_ms": result.elapsed_ms,
                    "character_count": result.character_count,
                    "confidence": result.confidence,
                    "quality_score": result.quality_score,
                    "quality_decision": result.quality_decision,
                    "fallback_count": len(result.fallbacks),
                    "cache_hit": result.cache_hit,
                    "page_count": result.page_count,
                    "warnings": result.warnings,
                }
            )
        elif fallbacks is not None:
            event["fallback_count"] = len(fallbacks)
            event["fallbacks"] = [item.model_dump() for item in fallbacks]

        logger.info("extraction_telemetry %s", event)
