"""OpenAI-compatible provider (OpenAI, Groq, Vercel AI Gateway, custom endpoints)."""

from __future__ import annotations

import json
import logging
from typing import AsyncGenerator, ClassVar, Sequence

import httpx

from app.ai.errors import RateLimitError
from app.ai.http_retry import post_json_with_retry
from app.ai.providers.base import (
    AIProvider,
    ChatMessage,
    EmbeddingVector,
    GenerationResult,
    HealthStatus,
    ProviderError,
    TokenUsage,
    TransientProviderError,
    ValidationProviderError,
)

logger = logging.getLogger(__name__)


def _map_http_error(exc: httpx.HTTPStatusError, label: str) -> ProviderError:
    status = exc.response.status_code if exc.response is not None else None
    detail = exc.response.text[:500] if exc.response is not None else str(exc)
    message = f"{label} API error {status}: {detail}"
    if status in {429, 500, 502, 503, 504}:
        return TransientProviderError(message)
    return ProviderError(message)


def _parse_usage(data: dict) -> TokenUsage | None:
    usage = data.get("usage")
    if not isinstance(usage, dict):
        return None
    return TokenUsage(
        prompt_tokens=usage.get("prompt_tokens"),
        completion_tokens=usage.get("completion_tokens"),
        total_tokens=usage.get("total_tokens"),
    )


class OpenAICompatibleProvider:
    """Thin OpenAI-compatible HTTP provider."""

    provider_name: ClassVar[str] = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        timeout_seconds: float = 60.0,
        supports_json_mode: bool = True,
        label: str | None = None,
    ) -> None:
        if not api_key:
            raise ProviderError(f"{label or self.provider_name} API key is not configured")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._supports_json_mode = supports_json_mode
        self._label = label or self.provider_name

    @property
    def provider_name(self) -> str:
        return self._label

    async def health_check(self) -> HealthStatus:
        try:
            async with httpx.AsyncClient(timeout=min(self._timeout, 10.0)) as client:
                response = await client.get(
                    f"{self._base_url}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                )
                if response.status_code == 429:
                    return HealthStatus(
                        healthy=False,
                        provider=self._label,
                        detail="rate_limited",
                    )
                healthy = response.status_code < 500
                return HealthStatus(
                    healthy=healthy,
                    provider=self._label,
                    detail=f"status={response.status_code}",
                )
        except httpx.HTTPError as exc:
            return HealthStatus(healthy=False, provider=self._label, detail=str(exc))

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        if not model:
            raise ValidationProviderError("Model is required")
        payload: dict = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._post_chat(payload)
        return self._parse_chat_response(data, model)

    async def stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> AsyncGenerator[str, None]:
        if not model:
            raise ValidationProviderError("Model is required")
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/chat/completions"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        await response.aread()
                        raise ProviderError(f"{self._label} stream API error {response.status_code}")
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                choices = data.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self._label} stream connection error: {exc}") from exc

    async def structured_output(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        if not model:
            raise ValidationProviderError("Model is required")
        payload: dict = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if self._supports_json_mode:
            payload["response_format"] = {"type": "json_object"}
        data = await self._post_chat(payload)
        return self._parse_chat_response(data, model)

    async def vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        model: str,
        mime_type: str = "image/jpeg",
        temperature: float = 0.0,
    ) -> GenerationResult:
        raise ProviderError(f"{self._label} does not support vision via OpenAI-compatible API")

    async def embed(
        self,
        text: str,
        *,
        model: str,
        dimensions: int,
    ) -> EmbeddingVector:
        results = await self.embed_many([text], model=model, dimensions=dimensions)
        return results[0]

    async def embed_many(
        self,
        texts: Sequence[str],
        *,
        model: str,
        dimensions: int,
    ) -> list[EmbeddingVector]:
        if not model:
            raise ValidationProviderError("Embedding model is required")
        if dimensions <= 0:
            raise ValidationProviderError("Embedding dimensions must be positive")

        cleaned = [text.strip() for text in texts]
        if not cleaned or any(not text for text in cleaned):
            raise ValidationProviderError("Cannot embed empty text")

        payload: dict = {
            "model": model,
            "input": cleaned if len(cleaned) > 1 else cleaned[0],
        }
        if model.startswith("text-embedding-3"):
            payload["dimensions"] = dimensions

        try:
            data = await post_json_with_retry(
                url=f"{self._base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                payload=payload,
                timeout=self._timeout,
                error_label=f"{self._label} Embeddings API",
            )
        except RateLimitError as exc:
            raise TransientProviderError(str(exc), retry_after_seconds=exc.retry_after_seconds) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc, self._label) from exc
        except httpx.HTTPError as exc:
            raise TransientProviderError(f"{self._label} embeddings request failed: {exc}") from exc

        try:
            items = sorted(data["data"], key=lambda item: item["index"])
            model_name = str(data.get("model", model))
        except (KeyError, TypeError) as exc:
            raise ProviderError(f"Unexpected {self._label} embedding response shape") from exc

        if len(items) != len(cleaned):
            raise ProviderError(f"Expected {len(cleaned)} embeddings, got {len(items)}")

        results: list[EmbeddingVector] = []
        for item in items:
            try:
                vector = [float(value) for value in item["embedding"]]
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderError("Invalid embedding vector in response") from exc

            if len(vector) != dimensions:
                raise ProviderError(f"Expected {dimensions} dimensions, got {len(vector)}")

            results.append(
                EmbeddingVector(
                    vector=vector,
                    model=model_name,
                    provider=self._label,
                    dimensions=dimensions,
                )
            )
        return results

    async def _post_chat(self, payload: dict) -> dict:
        try:
            return await post_json_with_retry(
                url=f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                payload=payload,
                timeout=self._timeout,
                error_label=f"{self._label} API",
            )
        except RateLimitError as exc:
            raise TransientProviderError(str(exc), retry_after_seconds=exc.retry_after_seconds) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc, self._label) from exc
        except httpx.HTTPError as exc:
            raise TransientProviderError(f"{self._label} request failed: {exc}") from exc

    def _parse_chat_response(self, data: dict, requested_model: str) -> GenerationResult:
        try:
            content = data["choices"][0]["message"]["content"]
            model = str(data.get("model", requested_model))
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected {self._label} response shape") from exc

        if not content or not str(content).strip():
            raise ProviderError(f"{self._label} returned empty content")

        finish_reason = None
        if isinstance(data.get("choices"), list) and data["choices"]:
            finish_reason = data["choices"][0].get("finish_reason")

        return GenerationResult(
            content=str(content).strip(),
            model=model,
            provider=self._label,
            usage=_parse_usage(data),
            finish_reason=str(finish_reason) if finish_reason else None,
        )


def supports_openai_compatible(provider: AIProvider) -> bool:
    return isinstance(provider, OpenAICompatibleProvider)
