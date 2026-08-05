"""Factory for registered AI providers."""

from __future__ import annotations

from typing import Callable

from app.ai.config import ProviderCredentials, resolve_provider_credentials
from app.ai.providers.base import AIProvider, ProviderError
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.ollama import OllamaProvider
from app.ai.providers.openai import OpenAICompatibleProvider
from app.ai.providers.xai import XAIProvider
from app.core.config.settings import Settings

ProviderFactory = Callable[[ProviderCredentials], AIProvider]

_REGISTRY: dict[str, ProviderFactory] = {}


def register_provider(name: str, factory: ProviderFactory) -> None:
    normalized = name.lower().strip()
    _REGISTRY[normalized] = factory


def registered_providers() -> frozenset[str]:
    return frozenset(_REGISTRY.keys())


def _register_defaults() -> None:
    if _REGISTRY:
        return

    register_provider(
        "openai",
        lambda creds: OpenAICompatibleProvider(
            api_key=creds.api_key,
            base_url=creds.base_url or "",
            timeout_seconds=creds.timeout_seconds,
            supports_json_mode=creds.supports_json_mode,
            label="openai",
        ),
    )
    register_provider(
        "groq",
        lambda creds: OpenAICompatibleProvider(
            api_key=creds.api_key,
            base_url=creds.base_url or "",
            timeout_seconds=creds.timeout_seconds,
            supports_json_mode=creds.supports_json_mode,
            label="groq",
        ),
    )
    register_provider(
        "vercel",
        lambda creds: OpenAICompatibleProvider(
            api_key=creds.api_key,
            base_url=creds.base_url or "",
            timeout_seconds=creds.timeout_seconds,
            supports_json_mode=creds.supports_json_mode,
            label="vercel",
        ),
    )
    register_provider(
        "ollama",
        lambda creds: OllamaProvider(
            api_key=creds.api_key,
            base_url=creds.base_url or "",
            timeout_seconds=creds.timeout_seconds,
        ),
    )
    register_provider(
        "gemini",
        lambda creds: GeminiProvider(
            api_key=creds.api_key,
            timeout_seconds=creds.timeout_seconds,
            api_base_url=creds.gemini_api_base_url,
        ),
    )
    register_provider(
        "xai",
        lambda creds: XAIProvider(
            api_key=creds.api_key,
            base_url=creds.base_url or "",
            timeout_seconds=creds.timeout_seconds,
        ),
    )


def create_provider(settings: Settings, provider_name: str) -> AIProvider:
    """Instantiate a provider by registration name."""
    _register_defaults()
    normalized = provider_name.lower().strip()
    aliases = {
        "openai_compatible": "openai",
        "openai-compatible": "openai",
        "grok": "xai",
        "local": "ollama",
        "google": "gemini",
    }
    normalized = aliases.get(normalized, normalized)

    factory = _REGISTRY.get(normalized)
    if factory is None:
        raise ProviderError(
            f"Unsupported AI provider: {provider_name}. "
            f"Registered: {', '.join(sorted(_REGISTRY.keys()))}"
        )

    credentials = resolve_provider_credentials(settings, normalized)
    if credentials.base_url is None and normalized not in {"gemini"}:
        raise ProviderError(f"Base URL is not configured for provider {normalized}")

    return factory(credentials)
