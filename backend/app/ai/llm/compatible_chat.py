"""OpenAI-compatible chat completions provider (httpx — no official SDK)."""

from __future__ import annotations

import logging

import httpx

from app.ai.http_retry import post_json_with_retry
from app.ai.llm.errors import LLMProviderError
from app.ai.llm.provider import ChatCompletion, ChatMessage

logger = logging.getLogger(__name__)


class OpenAICompatibleChatProvider:
    """Works with OpenAI, Groq, Vercel AI Gateway, Ollama, vLLM, and similar APIs."""

    def __init__(
        self,
        api_key: str,
        model: str,
        *,
        base_url: str,
        timeout_seconds: float = 60.0,
        supports_json_mode: bool = True,
        provider_label: str = "LLM",
    ) -> None:
        if not api_key:
            raise LLMProviderError(f"{provider_label} API key is not configured")
        if not model:
            raise LLMProviderError("LLM model is not configured")

        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._supports_json_mode = supports_json_mode
        self._provider_label = provider_label

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
        if self._supports_json_mode:
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
                error_label=f"{self._provider_label} API",
            )
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500] if exc.response is not None else str(exc)
            raise LLMProviderError(
                f"{self._provider_label} API error "
                f"{exc.response.status_code if exc.response else 'unknown'}: {detail}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMProviderError(f"{self._provider_label} request failed: {exc}") from exc

        try:
            content = data["choices"][0]["message"]["content"]
            model = data.get("model", self._model)
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError(f"Unexpected {self._provider_label} response shape") from exc

        if not content or not str(content).strip():
            raise LLMProviderError(f"{self._provider_label} returned empty content")

        return ChatCompletion(content=str(content).strip(), model=str(model))
