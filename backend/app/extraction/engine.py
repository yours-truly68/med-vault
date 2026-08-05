"""Extraction Engine orchestrator."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Mapping
from uuid import UUID

from app.core.config.settings import Settings
from app.extraction.cache import ExtractionCache
from app.extraction.exceptions import (
    AllExtractorsFailedError,
    ExtractionError,
)
from app.extraction.inspector import FileInspector
from app.extraction.models import (
    ExtractionHealthReport,
    ExtractionRequest,
    ExtractionResult,
    ExtractorName,
    FallbackAttempt,
    QualityDecision,
)
from app.extraction.quality import QualityScorer
from app.extraction.router import ExtractionRouter
from app.extraction.strategies.base import BaseExtractor
from app.extraction.strategies.docling import DoclingExtractor
from app.extraction.strategies.gemini_vision import GeminiVisionExtractor
from app.extraction.strategies.pymupdf import PyMuPdfExtractor
from app.extraction.strategies.tesseract import TesseractExtractor
from app.extraction.telemetry import ExtractionTelemetry

logger = logging.getLogger(__name__)

OCR_EXTRACTORS = frozenset({ExtractorName.TESSERACT, ExtractorName.GEMINI_VISION})


class ExtractionEngine:
    """Inspect → cache → route → quality-gated strategy chain."""

    def __init__(
        self,
        settings: Settings,
        *,
        inspector: FileInspector | None = None,
        router: ExtractionRouter | None = None,
        quality: QualityScorer | None = None,
        cache: ExtractionCache | None = None,
        telemetry: ExtractionTelemetry | None = None,
        extractors: Mapping[ExtractorName, BaseExtractor] | None = None,
    ) -> None:
        self._settings = settings
        self._inspector = inspector or FileInspector(settings)
        self._router = router or ExtractionRouter(settings)
        self._quality = quality or QualityScorer(
            accept_threshold=settings.extraction_quality_accept_threshold,
            warn_threshold=settings.extraction_quality_warn_threshold,
            w_printable=settings.extraction_w_printable,
            w_ocr_confidence=settings.extraction_w_ocr_confidence,
            w_density=settings.extraction_w_density,
            w_medical=settings.extraction_w_medical,
            w_garbled=settings.extraction_w_garbled,
        )
        cache_dir = Path(settings.extraction_cache_dir)
        if not cache_dir.is_absolute():
            cache_dir = Path.cwd() / cache_dir
        self._cache = cache or ExtractionCache(
            cache_dir,
            enabled=settings.extraction_cache_enabled,
            ttl_seconds=settings.extraction_cache_ttl_seconds,
        )
        self._telemetry = telemetry or ExtractionTelemetry()
        self._extractors: dict[ExtractorName, BaseExtractor] = dict(
            extractors
            or {
                ExtractorName.PYMUPDF: PyMuPdfExtractor(settings),
                ExtractorName.DOCLING: DoclingExtractor(settings),
                ExtractorName.TESSERACT: TesseractExtractor(settings),
                ExtractorName.GEMINI_VISION: GeminiVisionExtractor(settings),
            }
        )

    async def extract(
        self,
        path: Path,
        *,
        declared_content_type: str | None = None,
        document_id: UUID | None = None,
    ) -> ExtractionResult:
        started = time.perf_counter()
        probe = await self._inspector.inspect(
            path,
            declared_content_type=declared_content_type,
        )

        cached = await self._cache.get(probe.file_sha256)
        if cached is not None and cached.quality_score >= self._settings.extraction_quality_warn_threshold:
            cached.cache_hit = True
            self._telemetry.record(
                result=cached,
                document_id=document_id,
                mime_type=probe.mime_type,
                file_kind=probe.kind,
            )
            return cached

        plan = self._router.plan(probe)
        attempts: list[FallbackAttempt] = []
        best_rejected: ExtractionResult | None = None
        request = ExtractionRequest(path=path, probe=probe, document_id=document_id)

        for name in plan:
            extractor = self._extractors.get(name)
            if extractor is None or not extractor.supports(probe):
                continue

            attempt_started = time.perf_counter()
            try:
                raw = await asyncio.wait_for(
                    extractor.extract(request),
                    timeout=self._settings.extraction_timeout_seconds,
                )
                quality = self._quality.score(raw, is_ocr=name in OCR_EXTRACTORS)
                duration_ms = (time.perf_counter() - attempt_started) * 1000
                attempts.append(
                    FallbackAttempt(
                        extractor=name,
                        duration_ms=duration_ms,
                        quality_score=quality.score,
                        decision=quality.decision,
                    )
                )

                result = ExtractionResult(
                    text=raw.text,
                    extractor=name.value,
                    confidence=raw.extractor_confidence if raw.extractor_confidence is not None else quality.score,
                    quality_score=quality.score,
                    quality_decision=quality.decision,
                    character_count=len(raw.text),
                    page_count=raw.page_count,
                    elapsed_ms=int((time.perf_counter() - started) * 1000),
                    warnings=[*raw.warnings, *quality.reasons],
                    quality=quality,
                    fallbacks=list(attempts),
                    cache_hit=False,
                    file_sha256=probe.file_sha256,
                    page_results=raw.page_results,
                )

                if quality.decision in {
                    QualityDecision.ACCEPT,
                    QualityDecision.ACCEPT_WITH_WARN,
                }:
                    if quality.decision == QualityDecision.ACCEPT_WITH_WARN:
                        result.warnings = [
                            *result.warnings,
                            "accepted_with_quality_warning",
                        ]
                    await self._cache.put(probe.file_sha256, result)
                    self._telemetry.record(
                        result=result,
                        document_id=document_id,
                        mime_type=probe.mime_type,
                        file_kind=probe.kind,
                    )
                    return result

                if best_rejected is None or result.quality_score > best_rejected.quality_score:
                    best_rejected = result

            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - attempt_started) * 1000
                attempts.append(
                    FallbackAttempt(
                        extractor=name,
                        duration_ms=duration_ms,
                        error=f"timeout after {self._settings.extraction_timeout_seconds}s",
                    )
                )
                logger.warning(
                    "Extractor %s timed out for %s after %.0fs",
                    name.value,
                    path.name,
                    self._settings.extraction_timeout_seconds,
                )
                continue
            except ExtractionError as exc:
                duration_ms = (time.perf_counter() - attempt_started) * 1000
                attempts.append(
                    FallbackAttempt(
                        extractor=name,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                )
                logger.warning(
                    "Extractor %s failed for %s: %s",
                    name.value,
                    path.name,
                    exc,
                )
                continue
            except Exception as exc:
                duration_ms = (time.perf_counter() - attempt_started) * 1000
                attempts.append(
                    FallbackAttempt(
                        extractor=name,
                        duration_ms=duration_ms,
                        error=str(exc),
                    )
                )
                logger.exception("Unexpected extractor failure (%s)", name.value)
                continue

        if (
            best_rejected is not None
            and self._settings.extraction_allow_low_quality_last_resort
        ):
            best_rejected.quality_decision = QualityDecision.ACCEPT_WITH_WARN
            best_rejected.warnings = [
                *best_rejected.warnings,
                "low_quality_last_resort",
            ]
            best_rejected.elapsed_ms = int((time.perf_counter() - started) * 1000)
            best_rejected.fallbacks = list(attempts)
            await self._cache.put(probe.file_sha256, best_rejected)
            self._telemetry.record(
                result=best_rejected,
                document_id=document_id,
                mime_type=probe.mime_type,
                file_kind=probe.kind,
            )
            return best_rejected

        attempt_summaries = [
            f"{item.extractor.value}:{item.error or item.decision or 'unknown'}"
            for item in attempts
        ]
        error = AllExtractorsFailedError(
            f"All extractors failed or rejected for {path.name}",
            attempts=attempt_summaries,
        )
        self._telemetry.record(
            document_id=document_id,
            file_sha256=probe.file_sha256,
            mime_type=probe.mime_type,
            file_kind=probe.kind,
            error=str(error),
            fallbacks=attempts,
        )
        raise error

    async def health(self) -> ExtractionHealthReport:
        reports = []
        for extractor in self._extractors.values():
            try:
                reports.append(await extractor.health_check())
            except Exception as exc:
                from app.extraction.models import ExtractorHealth

                reports.append(
                    ExtractorHealth(
                        name=extractor.name,
                        healthy=False,
                        detail=str(exc),
                    )
                )
        return ExtractionHealthReport(
            healthy=any(item.healthy for item in reports),
            extractors=reports,
        )
