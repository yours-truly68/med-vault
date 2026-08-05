"""Ollama local provider (OpenAI-compatible API)."""

from __future__ import annotations

from typing import ClassVar

from app.ai.providers.openai import OpenAICompatibleProvider


class OllamaProvider(OpenAICompatibleProvider):
    """Local Ollama via OpenAI-compatible /v1 endpoints."""

    provider_name: ClassVar[str] = "ollama"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float = 60.0,
    ) -> None:
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            supports_json_mode=False,
            label=self.provider_name,
        )
