"""Common AI provider interface and shared types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class GenerationResult:
    content: str
    model: str
    provider: str
    usage: TokenUsage | None = None


@dataclass(frozen=True)
class EmbeddingVector:
    vector: list[float]
    model: str
    provider: str
    dimensions: int


@dataclass(frozen=True)
class HealthStatus:
    healthy: bool
    provider: str
    detail: str = ""


class ProviderError(Exception):
    """Non-retryable provider failure."""


class TransientProviderError(ProviderError):
    """Retryable provider failure (rate limit, timeout, temporary outage)."""

    def __init__(
        self,
        message: str,
        *,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ValidationProviderError(ProviderError):
    """Input or response validation failure — never retry."""


class AIProvider(Protocol):
    @property
    def provider_name(self) -> str:
        """Registered provider identifier."""
        ...

    async def health_check(self) -> HealthStatus:
        ...

    async def generate(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        ...

    async def structured_output(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        ...

    async def vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        model: str,
        mime_type: str = "image/jpeg",
        temperature: float = 0.0,
    ) -> GenerationResult:
        ...

    async def embed(
        self,
        text: str,
        *,
        model: str,
        dimensions: int,
    ) -> EmbeddingVector:
        ...

    async def embed_many(
        self,
        texts: Sequence[str],
        *,
        model: str,
        dimensions: int,
    ) -> list[EmbeddingVector]:
        ...
