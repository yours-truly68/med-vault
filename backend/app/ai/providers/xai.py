"""xAI (Grok) provider via OpenAI-compatible API."""

from __future__ import annotations

from typing import ClassVar

from app.ai.providers.openai import OpenAICompatibleProvider


class XAIProvider(OpenAICompatibleProvider):
    """Grok models via xAI's OpenAI-compatible endpoint."""

    provider_name: ClassVar[str] = "xai"

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
            supports_json_mode=True,
            label=self.provider_name,
        )
