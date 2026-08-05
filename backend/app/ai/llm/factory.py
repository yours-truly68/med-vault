"""Factory for LLM providers."""

from __future__ import annotations

from app.ai.llm.compatible_chat import OpenAICompatibleChatProvider
from app.ai.llm.config import resolve_llm_config
from app.ai.llm.errors import LLMProviderError
from app.ai.llm.provider import LLMProvider
from app.core.config.settings import Settings

SUPPORTED_LLM_PROVIDERS = frozenset({
    "openai",
    "groq",
    "vercel",
    "ollama",
    "local",
    "openai_compatible",
    "openai-compatible",
})


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        raise LLMProviderError(
            f"Unsupported LLM provider: {settings.llm_provider}. "
            f"Supported: {', '.join(sorted(SUPPORTED_LLM_PROVIDERS))}"
        )

    config = resolve_llm_config(settings)
    return OpenAICompatibleChatProvider(
        api_key=config.api_key,
        model=config.model,
        base_url=config.base_url,
        timeout_seconds=config.timeout_seconds,
        supports_json_mode=config.supports_json_mode,
        provider_label=config.provider,
    )
