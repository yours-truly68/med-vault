"""Resolve LLM runtime configuration from application settings."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config.settings import Settings

# OpenAI-compatible HTTP APIs (OpenAI, Groq, Vercel AI Gateway, Ollama, vLLM, etc.)
PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "openai_api_key",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key_env": "groq_api_key",
    },
    "vercel": {
        "base_url": "https://ai-gateway.vercel.sh/v1",
        "api_key_env": "vercel_ai_api_key",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "ollama_api_key",
    },
    "local": {
        "base_url": "http://localhost:11434/v1",
        "api_key_env": "local_llm_api_key",
    },
}


@dataclass(frozen=True)
class LLMRuntimeConfig:
    provider: str
    api_key: str
    base_url: str
    model: str
    timeout_seconds: float
    supports_json_mode: bool


def _resolve_api_key(settings: Settings, provider: str, defaults: dict[str, str]) -> str:
    generic = (settings.llm_api_key or "").strip()
    if generic:
        return generic

    env_field = defaults.get("api_key_env", "openai_api_key")
    provider_key = getattr(settings, env_field, None)
    if provider_key:
        return str(provider_key).strip()

    # Fall back to OpenAI key for openai-compatible custom endpoints.
    if settings.openai_api_key:
        return settings.openai_api_key.strip()

    # Local providers often accept any non-empty bearer token.
    if provider in {"ollama", "local"}:
        return "ollama"

    return ""


def resolve_llm_config(settings: Settings) -> LLMRuntimeConfig:
    provider = settings.llm_provider.lower().strip()
    alias = {
        "openai_compatible": "openai",
        "openai-compatible": "openai",
    }.get(provider, provider)

    defaults = PROVIDER_DEFAULTS.get(alias, PROVIDER_DEFAULTS["openai"])
    base_url = (settings.llm_base_url or settings.openai_base_url or defaults["base_url"]).rstrip("/")
    api_key = _resolve_api_key(settings, alias, defaults)

    supports_json_mode = "ai-gateway.vercel.sh" not in base_url and alias not in {
        "ollama",
        "local",
    }

    return LLMRuntimeConfig(
        provider=alias,
        api_key=api_key,
        base_url=base_url,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
        supports_json_mode=supports_json_mode,
    )
