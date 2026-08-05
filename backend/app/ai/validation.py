"""Startup validation for AI and extraction configuration."""

from __future__ import annotations

import logging

from app.ai.capabilities import (
    IMPLEMENTED_PROVIDER_CAPABILITIES,
    REGISTERED_PROVIDERS,
    TASK_REQUIRED_CAPABILITIES,
    find_capability_mismatches,
    get_provider_capabilities,
    provider_supports_task,
)
from app.ai.config import AITask, resolve_provider_credentials, resolve_task_routes
from app.core.config.settings import Settings
from app.extraction.models import ExtractorName

logger = logging.getLogger(__name__)

KNOWN_PROVIDERS = REGISTERED_PROVIDERS | frozenset({"local", "openai_compatible", "google"})
KNOWN_EXTRACTORS = frozenset(name.value for name in ExtractorName)


class ConfigurationError(Exception):
    """Raised when environment configuration is invalid."""


def _warn_legacy_env_usage(settings: Settings) -> None:
    import os

    legacy_map = {
        "DEFAULT_BASE_URL": "VERCEL_BASE_URL or OPENAI_BASE_URL",
        "OPENAI_BASE_URL": "VERCEL_BASE_URL (for gateway) or provider-specific base URL fields",
    }
    for legacy, preferred in legacy_map.items():
        if os.getenv(legacy) and not os.getenv("VERCEL_BASE_URL"):
            logger.warning(
                "Deprecated env var %s is set; prefer %s",
                legacy,
                preferred,
            )


def _validate_provider_field(task_label: str, provider: str | None, model: str | None) -> None:
    if not provider or not provider.strip():
        raise ConfigurationError(f"{task_label}_PROVIDER is required")
    if not model or not model.strip():
        raise ConfigurationError(f"{task_label}_MODEL is required")

    normalized = provider.strip().lower()
    if normalized not in KNOWN_PROVIDERS:
        raise ConfigurationError(
            f"{task_label}_PROVIDER={provider!r} is not a known provider. "
            f"Expected one of: {', '.join(sorted(KNOWN_PROVIDERS))}"
        )
    if "/" in provider or ":" in provider:
        raise ConfigurationError(
            f"{task_label}_PROVIDER={provider!r} looks like a model or gateway path. "
            f"Put model ids in {task_label}_MODEL only."
        )


def _validate_extractor_name(field: str, value: str | None, *, required: bool = False) -> None:
    if not value or not value.strip():
        if required:
            raise ConfigurationError(f"{field} is required")
        return
    normalized = value.strip().lower().replace("-", "_")
    aliases = {"gemini": "gemini_vision"}
    resolved = aliases.get(normalized, normalized)
    if resolved not in KNOWN_EXTRACTORS:
        raise ConfigurationError(
            f"{field}={value!r} is not a known extractor. "
            f"Expected one of: {', '.join(sorted(KNOWN_EXTRACTORS))}"
        )


def validate_provider_capability_matrix() -> None:
    """Ensure the capability registry matches provider implementations."""
    mismatches = find_capability_mismatches(IMPLEMENTED_PROVIDER_CAPABILITIES)
    if mismatches:
        detail = "\n  - ".join(mismatches)
        raise ConfigurationError(f"Provider capability matrix mismatch:\n  - {detail}")


def validate_ai_configuration(settings: Settings) -> None:
    """Validate AI routes, credentials, and provider capabilities at startup."""
    validate_provider_capability_matrix()
    _warn_legacy_env_usage(settings)

    routes = resolve_task_routes(settings)
    errors: list[str] = []

    task_labels = {
        AITask.CLASSIFICATION: "CLASSIFICATION",
        AITask.METADATA: "METADATA",
        AITask.SUMMARY: "SUMMARY",
        AITask.VISION: "VISION",
        AITask.CHAT: "CHAT",
        AITask.EMBEDDING: "EMBEDDING",
    }

    for task, label in task_labels.items():
        route = routes[task]
        try:
            _validate_provider_field(label, route.provider, route.model)
        except ConfigurationError as exc:
            errors.append(str(exc))
            continue

        if not provider_supports_task(route.provider, task):
            caps = get_provider_capabilities(route.provider)
            required_attrs = TASK_REQUIRED_CAPABILITIES.get(task, ())
            errors.append(
                f"{label} provider {route.provider!r} lacks required capabilities "
                f"({', '.join(required_attrs)}) for {task.value}"
            )
            if caps is None:
                errors.append(f"Unknown provider capabilities for {route.provider!r}")

        try:
            resolve_provider_credentials(settings, route.provider)
        except ValueError as exc:
            errors.append(f"{label}: {exc}")

        if route.fallback_provider:
            try:
                _validate_provider_field(f"{label}_FALLBACK", route.fallback_provider, route.fallback_model or "")
                if not provider_supports_task(route.fallback_provider, task):
                    errors.append(
                        f"{label} fallback provider {route.fallback_provider!r} "
                        f"does not support {task.value}"
                    )
                resolve_provider_credentials(settings, route.fallback_provider)
            except ConfigurationError as exc:
                errors.append(str(exc))
            except ValueError as exc:
                errors.append(f"{label} fallback: {exc}")

    if errors:
        detail = "\n  - ".join(errors)
        raise ConfigurationError(f"Invalid AI configuration:\n  - {detail}")


def validate_extraction_configuration(settings: Settings) -> None:
    """Validate extraction engine configuration at startup."""
    errors: list[str] = []

    _validate_extractor_name("PRIMARY_PDF_EXTRACTOR", settings.primary_pdf_extractor, required=True)
    _validate_extractor_name("SECONDARY_PDF_EXTRACTOR", settings.secondary_pdf_extractor)
    _validate_extractor_name("IMAGE_EXTRACTOR", settings.image_extractor, required=True)
    _validate_extractor_name("VISION_FALLBACK", settings.vision_fallback)

    secondary = (settings.secondary_pdf_extractor or "").strip().lower()
    if secondary == "docling" and not settings.docling_enabled:
        errors.append("SECONDARY_PDF_EXTRACTOR=docling requires DOCLING_ENABLED=true")

    if settings.tesseract_enabled and not settings.tesseract_cmd:
        logger.info(
            "TESSERACT_CMD is unset; relying on tesseract binary on PATH"
        )

    if errors:
        detail = "\n  - ".join(errors)
        raise ConfigurationError(f"Invalid extraction configuration:\n  - {detail}")


def validate_application_configuration(settings: Settings) -> None:
    """Validate all configuration domains."""
    validate_extraction_configuration(settings)
    validate_ai_configuration(settings)
