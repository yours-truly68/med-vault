"""Centralized AI task routing and provider credentials."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum

from app.core.config.settings import Settings
from app.core.database.enums import EMBEDDING_DIMENSIONS

logger = logging.getLogger(__name__)


class AITask(StrEnum):
    CLASSIFICATION = "classification"
    METADATA = "metadata"
    SUMMARY = "summary"
    EMBEDDING = "embedding"
    CHAT = "chat"


@dataclass(frozen=True)
class TaskRoute:
    """Primary and optional fallback routing for one AI task."""

    task: AITask
    provider: str
    model: str
    fallback_provider: str | None = None
    fallback_model: str | None = None


@dataclass(frozen=True)
class ProviderCredentials:
    """Resolved credentials for a provider registration."""

    provider: str
    api_key: str
    base_url: str | None = None
    timeout_seconds: float = 60.0
    supports_json_mode: bool = True
    embedding_dimensions: int = EMBEDDING_DIMENSIONS
    gemini_api_base_url: str | None = None


def _normalize_provider_name(name: str) -> str:
    normalized = name.lower().strip()
    aliases = {
        "openai_compatible": "openai",
        "openai-compatible": "openai",
        "grok": "xai",
        "local": "ollama",
        "google": "gemini",
    }
    return aliases.get(normalized, normalized)


def _provider_api_key_field(provider: str) -> str:
    return {
        "openai": "openai_api_key",
        "groq": "groq_api_key",
        "vercel": "vercel_ai_api_key",
    }.get(provider, "openai_api_key")


def _provider_base_url(settings: Settings, provider: str) -> str:
    if provider == "openai":
        return (settings.llm_base_url or settings.openai_base_url or settings.openai_default_base_url).rstrip("/")
    if provider == "groq":
        return settings.groq_base_url.rstrip("/")
    if provider == "vercel":
        return settings.vercel_base_url.rstrip("/")
    if provider == "xai":
        return settings.xai_base_url.rstrip("/")
    if provider == "ollama":
        host = settings.ollama_host.rstrip("/")
        return f"{host}/v1"
    raise ValueError(f"No base URL configured for provider {provider!r}")


def _resolve_openai_compat_key(settings: Settings, provider: str) -> str:
    generic = (settings.llm_api_key or "").strip()
    if generic:
        return generic

    field = _provider_api_key_field(provider)
    provider_key = getattr(settings, field, None)
    if provider_key:
        return str(provider_key).strip()

    if settings.openai_api_key:
        return settings.openai_api_key.strip()
    return ""


def resolve_provider_credentials(settings: Settings, provider: str) -> ProviderCredentials:
    """Resolve API key, base URL, and timeouts for a registered provider."""
    normalized = _normalize_provider_name(provider)

    if normalized == "gemini":
        api_key = (settings.gemini_api_key or "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured")
        return ProviderCredentials(
            provider=normalized,
            api_key=api_key,
            timeout_seconds=settings.llm_timeout_seconds,
            gemini_api_base_url=settings.gemini_api_base_url.rstrip("/"),
        )

    if normalized == "xai":
        api_key = (settings.xai_api_key or "").strip()
        if not api_key:
            raise ValueError("XAI_API_KEY is not configured")
        return ProviderCredentials(
            provider=normalized,
            api_key=api_key,
            base_url=_provider_base_url(settings, normalized),
            timeout_seconds=settings.llm_timeout_seconds,
            supports_json_mode=True,
        )

    if normalized == "ollama":
        api_key = (settings.ollama_api_key or "ollama").strip()
        return ProviderCredentials(
            provider=normalized,
            api_key=api_key,
            base_url=_provider_base_url(settings, normalized),
            timeout_seconds=settings.llm_timeout_seconds,
            supports_json_mode=False,
        )

    base_url = _provider_base_url(settings, normalized)
    api_key = _resolve_openai_compat_key(settings, normalized)
    if not api_key:
        key_name = _provider_api_key_field(normalized).upper()
        raise ValueError(f"{key_name} (or LLM_API_KEY / OPENAI_API_KEY) is not configured")

    supports_json_mode = normalized not in {"ollama"} and "ai-gateway.vercel.sh" not in base_url

    return ProviderCredentials(
        provider=normalized,
        api_key=api_key,
        base_url=base_url,
        timeout_seconds=settings.llm_timeout_seconds,
        supports_json_mode=supports_json_mode,
        embedding_dimensions=settings.embedding_dimensions or EMBEDDING_DIMENSIONS,
    )


def _route(
    settings: Settings,
    task: AITask,
    provider: str,
    model: str,
    fallback_provider: str | None,
    fallback_model: str | None,
) -> TaskRoute:
    return TaskRoute(
        task=task,
        provider=_normalize_provider_name(provider),
        model=model.strip(),
        fallback_provider=(
            _normalize_provider_name(fallback_provider)
            if fallback_provider and fallback_provider.strip()
            else None
        ),
        fallback_model=(
            fallback_model.strip()
            if fallback_provider
            and fallback_provider.strip()
            and fallback_model
            and fallback_model.strip()
            else None
        ),
    )


def _resolve_task_provider_model(
    settings: Settings,
    *,
    provider: str | None,
    model: str | None,
    default_provider: str,
    default_model: str,
    task_label: str,
) -> tuple[str, str]:
    resolved_provider = provider or default_provider
    resolved_model = model or default_model
    if not resolved_provider or not resolved_provider.strip():
        raise ValueError(f"{task_label}_PROVIDER (or LLM_PROVIDER) is required")
    if not resolved_model or not resolved_model.strip():
        raise ValueError(f"{task_label}_MODEL (or LLM_MODEL) is required")
    return resolved_provider.strip(), resolved_model.strip()


def resolve_task_routes(settings: Settings) -> dict[AITask, TaskRoute]:
    """Build task routing table from environment configuration."""
    legacy_provider = _normalize_provider_name(settings.llm_provider)
    legacy_model = settings.llm_model

    classification_provider, classification_model = _resolve_task_provider_model(
        settings,
        provider=settings.classification_provider,
        model=settings.classification_model,
        default_provider=legacy_provider,
        default_model=legacy_model,
        task_label="CLASSIFICATION",
    )

    metadata_provider, metadata_model = _resolve_task_provider_model(
        settings,
        provider=settings.metadata_provider,
        model=settings.metadata_model,
        default_provider=classification_provider,
        default_model=classification_model,
        task_label="METADATA",
    )

    summary_provider, summary_model = _resolve_task_provider_model(
        settings,
        provider=settings.summary_provider,
        model=settings.summary_model,
        default_provider=legacy_provider,
        default_model=legacy_model,
        task_label="SUMMARY",
    )

    chat_provider, chat_model = _resolve_task_provider_model(
        settings,
        provider=settings.chat_provider,
        model=settings.chat_model,
        default_provider=legacy_provider,
        default_model=legacy_model,
        task_label="CHAT",
    )

    embedding_provider = _normalize_provider_name(settings.embedding_provider or legacy_provider)
    embedding_model = settings.embedding_model or legacy_model
    if not embedding_model.strip():
        raise ValueError("EMBEDDING_MODEL (or LLM_MODEL) is required")

    return {
        AITask.CLASSIFICATION: _route(
            settings,
            AITask.CLASSIFICATION,
            classification_provider,
            classification_model,
            settings.classification_fallback_provider,
            settings.classification_fallback_model,
        ),
        AITask.METADATA: _route(
            settings,
            AITask.METADATA,
            metadata_provider,
            metadata_model,
            settings.metadata_fallback_provider,
            settings.metadata_fallback_model,
        ),
        AITask.SUMMARY: _route(
            settings,
            AITask.SUMMARY,
            summary_provider,
            summary_model,
            settings.summary_fallback_provider,
            settings.summary_fallback_model,
        ),
        AITask.CHAT: _route(
            settings,
            AITask.CHAT,
            chat_provider,
            chat_model,
            settings.chat_fallback_provider,
            settings.chat_fallback_model,
        ),
        AITask.EMBEDDING: _route(
            settings,
            AITask.EMBEDDING,
            embedding_provider,
            embedding_model,
            settings.embedding_fallback_provider,
            settings.embedding_fallback_model,
        ),
    }
