"""Google Gemini provider (generate, vision, embeddings)."""

from __future__ import annotations

import base64
import logging
from typing import ClassVar, Sequence

import httpx

from app.ai.errors import RateLimitError
from app.ai.http_retry import post_json_with_retry
from app.ai.providers.base import (
    ChatMessage,
    EmbeddingVector,
    GenerationResult,
    HealthStatus,
    ProviderError,
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


class GeminiProvider:
    provider_name: ClassVar[str] = "gemini"

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 90.0,
        api_base_url: str | None = None,
    ) -> None:
        if not api_key:
            raise ProviderError("Gemini API key is not configured")
        self._api_key = api_key
        self._timeout = timeout_seconds
        self._api_base = (api_base_url or "").rstrip("/")
        if not self._api_base:
            raise ProviderError("GEMINI_API_BASE_URL is not configured")

    @property
    def provider_name(self) -> str:
        return GeminiProvider.provider_name

    async def health_check(self) -> HealthStatus:
        try:
            async with httpx.AsyncClient(timeout=min(self._timeout, 10.0)) as client:
                response = await client.get(
                    f"{self._api_base}/models",
                    params={"key": self._api_key},
                )
                if response.status_code == 429:
                    return HealthStatus(healthy=False, provider="gemini", detail="rate_limited")
                healthy = response.status_code < 500
                return HealthStatus(
                    healthy=healthy,
                    provider="gemini",
                    detail=f"status={response.status_code}",
                )
        except httpx.HTTPError as exc:
            return HealthStatus(healthy=False, provider="gemini", detail=str(exc))

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
        text = self._messages_to_text(messages)
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        data = await self._post_generate(model, payload)
        return self._parse_generate_response(data, model)

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
        text = self._messages_to_text(messages)
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        }
        data = await self._post_generate(model, payload)
        return self._parse_generate_response(data, model)

    async def vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        model: str,
        mime_type: str = "image/jpeg",
        temperature: float = 0.0,
    ) -> GenerationResult:
        """[Deprecated] Vision processing is not enabled in current MVP."""
        raise NotImplementedError("Vision processing is not enabled in the current MVP release.")

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

        url = f"{self._api_base}/models/{model}:batchEmbedContents"
        requests = [
            {
                "model": f"models/{model}",
                "content": {"parts": [{"text": text}]},
                "outputDimensionality": dimensions,
            }
            for text in cleaned
        ]
        payload = {"requests": requests}

        try:
            data = await post_json_with_retry(
                url=url,
                headers={"Content-Type": "application/json"},
                payload=payload,
                timeout=self._timeout,
                error_label="Gemini Embeddings API",
                extra_params={"key": self._api_key},
            )
        except RateLimitError as exc:
            raise TransientProviderError(str(exc), retry_after_seconds=exc.retry_after_seconds) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc, "gemini") from exc
        except httpx.HTTPError as exc:
            raise TransientProviderError(f"Gemini embeddings request failed: {exc}") from exc

        try:
            embeddings = data["embeddings"]
        except (KeyError, TypeError) as exc:
            raise ProviderError("Unexpected Gemini embedding response shape") from exc

        if len(embeddings) != len(cleaned):
            raise ProviderError(f"Expected {len(cleaned)} embeddings, got {len(embeddings)}")

        results: list[EmbeddingVector] = []
        for item in embeddings:
            try:
                values = item["values"]
                vector = [float(value) for value in values]
            except (KeyError, TypeError, ValueError) as exc:
                raise ProviderError("Invalid Gemini embedding vector") from exc

            if len(vector) != dimensions:
                raise ProviderError(f"Expected {dimensions} dimensions, got {len(vector)}")

            results.append(
                EmbeddingVector(
                    vector=vector,
                    model=model,
                    provider="gemini",
                    dimensions=dimensions,
                )
            )
        return results

    async def _post_generate(self, model: str, payload: dict) -> dict:
        url = f"{self._api_base}/models/{model}:generateContent"
        try:
            return await post_json_with_retry(
                url=url,
                headers={"Content-Type": "application/json"},
                payload=payload,
                timeout=self._timeout,
                error_label="Gemini API",
                extra_params={"key": self._api_key},
            )
        except RateLimitError as exc:
            raise TransientProviderError(str(exc), retry_after_seconds=exc.retry_after_seconds) from exc
        except httpx.HTTPStatusError as exc:
            raise _map_http_error(exc, "gemini") from exc
        except httpx.HTTPError as exc:
            raise TransientProviderError(f"Gemini request failed: {exc}") from exc

    def _parse_generate_response(self, data: dict, requested_model: str) -> GenerationResult:
        try:
            parts = data["candidates"][0]["content"]["parts"]
            texts = [part.get("text", "") for part in parts if isinstance(part, dict)]
            content = "\n".join(text for text in texts if text).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"Unexpected Gemini response shape: {exc}") from exc

        if not content:
            raise ProviderError("Gemini returned empty content")

        return GenerationResult(
            content=content,
            model=requested_model,
            provider="gemini",
        )

    def _messages_to_text(self, messages: Sequence[ChatMessage]) -> str:
        if not messages:
            raise ValidationProviderError("At least one message is required")
        if len(messages) == 1:
            return messages[0].content
        lines = [f"{message.role}: {message.content}" for message in messages]
        return "\n\n".join(lines)
