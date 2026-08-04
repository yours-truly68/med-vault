"""Factory for LLM providers."""

from __future__ import annotations

from app.ai.llm.openai_provider import LLMProviderError, OpenAIProvider
from app.ai.llm.provider import LLMProvider
from app.core.config.settings import Settings


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key or "",
            model=settings.llm_model,
            base_url=settings.openai_base_url,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    raise LLMProviderError(f"Unsupported LLM provider: {settings.llm_provider}")
