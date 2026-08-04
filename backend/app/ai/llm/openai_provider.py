"""OpenAI Chat Completions provider (httpx — no official SDK)."""

from __future__ import annotations

import logging

import httpx

from app.ai.http_retry import post_json_with_retry
from app.ai.llm.provider import ChatCompletion, ChatMessage

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.openai.com/v1"


class LLMProviderError(Exception):
    """Raised when the LLM provider request fails."""


class OpenAIProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: float = 60.0,
    ) -> None:
        if not api_key:
            raise LLMProviderError("OpenAI API key is not configured")
        if not model:
            raise LLMProviderError("LLM model is not configured")

        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatCompletion:
        payload: dict = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Vercel AI Gateway rejects OpenAI's legacy json_object response_format.
        if "ai-gateway.vercel.sh" not in self._base_url:
            payload["response_format"] = {"type": "json_object"}

        try:
            data = await post_json_with_retry(
                url=f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                payload=payload,
                timeout=self._timeout,
                error_label="OpenAI API",
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMProviderError(
                f"OpenAI API error {exc.response.status_code if exc.response else 'unknown'}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"OpenAI request failed: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            model = data.get("model", self._model)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("Unexpected OpenAI response shape") from exc

        if not content or not str(content).strip():
            raise LLMProviderError("OpenAI returned empty content")

        return ChatCompletion(content=str(content).strip(), model=str(model))
