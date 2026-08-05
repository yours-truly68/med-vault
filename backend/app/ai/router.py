"""AI task router with failover, retries, and observability."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Sequence

from app.ai.capabilities import provider_supports_task
from app.ai.config import AITask, TaskRoute, resolve_task_routes
from app.ai.factory import create_provider
from app.ai.providers.base import (
    AIProvider,
    ChatMessage,
    EmbeddingVector,
    GenerationResult,
    HealthStatus,
    ProviderError,
    TransientProviderError,
    ValidationProviderError,
)
from app.core.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class _CachedHealth:
    status: HealthStatus
    expires_at: float


@dataclass(frozen=True)
class RouterExecutionMeta:
    task: AITask
    provider: str
    model: str
    latency_ms: float
    success: bool
    retry_count: int
    fallback_used: bool
    usage_prompt_tokens: int | None = None
    usage_completion_tokens: int | None = None
    usage_total_tokens: int | None = None
    error: str | None = None


class AITaskRouter:
    """Routes AI operations to task-configured providers with graceful failover."""

    def __init__(
        self,
        settings: Settings,
        *,
        max_retries: int | None = None,
        base_delay_seconds: float | None = None,
        max_delay_seconds: float | None = None,
        health_check_ttl_seconds: float | None = None,
    ) -> None:
        self._settings = settings
        self._routes = resolve_task_routes(settings)
        self._max_retries = max(1, max_retries or settings.ai_router_max_retries)
        self._base_delay = base_delay_seconds or settings.ai_router_base_delay_seconds
        self._max_delay = max_delay_seconds or settings.ai_router_max_delay_seconds
        self._health_ttl = health_check_ttl_seconds or settings.ai_health_check_ttl_seconds
        self._provider_cache: dict[str, AIProvider] = {}
        self._health_cache: dict[str, _CachedHealth] = {}

    def route_for(self, task: AITask) -> TaskRoute:
        return self._routes[task]

    async def health_check_task(self, task: AITask) -> HealthStatus:
        route = self._routes[task]
        provider = self._get_provider(route.provider)
        return await provider.health_check()

    def _get_provider(self, provider_name: str) -> AIProvider:
        if provider_name not in self._provider_cache:
            self._provider_cache[provider_name] = create_provider(
                self._settings, provider_name
            )
        return self._provider_cache[provider_name]

    def _route_candidates(self, task: AITask) -> list[tuple[str, str]]:
        route = self._routes[task]
        candidates: list[tuple[str, str]] = [(route.provider, route.model)]
        if route.fallback_provider and route.fallback_model:
            candidates.append((route.fallback_provider, route.fallback_model))
        return candidates

    async def _ensure_healthy(self, provider_name: str, task: AITask) -> bool:
        if not provider_supports_task(provider_name, task):
            logger.warning(
                "AI provider lacks capability for task: provider=%s task=%s",
                provider_name,
                task,
            )
            return False

        now = time.monotonic()
        cached = self._health_cache.get(provider_name)
        if cached is not None and cached.expires_at > now:
            return cached.status.healthy

        provider = self._get_provider(provider_name)
        health = await provider.health_check()
        self._health_cache[provider_name] = _CachedHealth(
            status=health,
            expires_at=now + self._health_ttl,
        )
        if not health.healthy:
            logger.warning(
                "AI provider unhealthy before dispatch: provider=%s detail=%s",
                provider_name,
                health.detail,
            )
        return health.healthy

    def _compute_delay(self, attempt: int, error: TransientProviderError) -> float:
        if error.retry_after_seconds is not None:
            return min(error.retry_after_seconds, self._max_delay)
        return min(self._base_delay * (2 ** (attempt - 1)), self._max_delay)

    def _log_execution(self, meta: RouterExecutionMeta) -> None:
        logger.info(
            "AI router: task=%s provider=%s model=%s latency_ms=%.0f success=%s "
            "retries=%s fallback=%s prompt_tokens=%s completion_tokens=%s total_tokens=%s error=%s",
            meta.task,
            meta.provider,
            meta.model,
            meta.latency_ms,
            meta.success,
            meta.retry_count,
            meta.fallback_used,
            meta.usage_prompt_tokens,
            meta.usage_completion_tokens,
            meta.usage_total_tokens,
            meta.error,
        )

    async def _execute_with_retries(
        self,
        task: AITask,
        provider_name: str,
        model: str,
        operation,
    ) -> tuple[GenerationResult | EmbeddingVector | list[EmbeddingVector], int]:
        retry_count = 0
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = await operation(provider_name, model)
                return result, retry_count
            except ValidationProviderError as exc:
                raise ProviderError(str(exc)) from exc
            except TransientProviderError as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    break
                retry_count += 1
                delay = self._compute_delay(attempt, exc)
                logger.warning(
                    "AI transient failure: task=%s provider=%s attempt=%s/%s delay=%.1fs error=%s",
                    task,
                    provider_name,
                    attempt,
                    self._max_retries,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
            except ProviderError as exc:
                last_error = exc
                break

        if last_error is not None:
            raise last_error
        raise ProviderError(f"AI task {task} failed without a captured error")

    async def generate(
        self,
        task: AITask,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        return await self._dispatch_generation(
            task,
            lambda provider_name, model: self._get_provider(provider_name).generate(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
        )

    async def structured_output(
        self,
        task: AITask,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> GenerationResult:
        return await self._dispatch_generation(
            task,
            lambda provider_name, model: self._get_provider(provider_name).structured_output(
                messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
            ),
        )

    async def vision(
        self,
        prompt: str,
        image_bytes: bytes,
        *,
        mime_type: str = "image/jpeg",
        temperature: float = 0.0,
    ) -> GenerationResult:
        """[Deprecated] Vision-based generation is not supported in MVP."""
        raise NotImplementedError("Vision is not supported in the current MVP release.")

    async def embed(self, text: str) -> EmbeddingVector:
        task = AITask.EMBEDDING
        dimensions = self._settings.embedding_dimensions

        async def operation(provider_name: str, model: str) -> EmbeddingVector:
            return await self._get_provider(provider_name).embed(
                text,
                model=model,
                dimensions=dimensions,
            )

        return await self._dispatch_single(task, operation)

    async def embed_many(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        task = AITask.EMBEDDING
        dimensions = self._settings.embedding_dimensions

        async def operation(provider_name: str, model: str) -> list[EmbeddingVector]:
            return await self._get_provider(provider_name).embed_many(
                texts,
                model=model,
                dimensions=dimensions,
            )

        return await self._dispatch_single(task, operation)

    async def _dispatch_single(self, task: AITask, operation) -> object:
        candidates = self._route_candidates(task)
        errors: list[str] = []

        for index, (provider_name, model) in enumerate(candidates):
            fallback_used = index > 0
            if not await self._ensure_healthy(provider_name, task):
                errors.append(f"{provider_name}: unhealthy")
                continue

            started = time.perf_counter()
            try:
                result, retry_count = await self._execute_with_retries(
                    task,
                    provider_name,
                    model,
                    operation,
                )
                latency_ms = (time.perf_counter() - started) * 1000
                self._log_result(task, provider_name, result, model, latency_ms, True, retry_count, fallback_used)
                return result
            except ProviderError as exc:
                latency_ms = (time.perf_counter() - started) * 1000
                errors.append(f"{provider_name}: {exc}")
                self._log_failure(task, provider_name, model, latency_ms, fallback_used, str(exc))

        detail = "; ".join(errors) if errors else "no providers configured"
        raise ProviderError(f"AI task {task} failed after failover: {detail}")

    def _log_result(
        self,
        task: AITask,
        provider_name: str,
        result: object,
        requested_model: str,
        latency_ms: float,
        success: bool,
        retry_count: int,
        fallback_used: bool,
    ) -> None:
        model = requested_model
        usage_prompt: int | None = None
        usage_completion: int | None = None
        usage_total: int | None = None

        if isinstance(result, GenerationResult):
            model = result.model
            if result.usage:
                usage_prompt = result.usage.prompt_tokens
                usage_completion = result.usage.completion_tokens
                usage_total = result.usage.total_tokens
        elif isinstance(result, EmbeddingVector):
            model = result.model
        elif isinstance(result, list) and result and isinstance(result[0], EmbeddingVector):
            model = result[0].model

        self._log_execution(
            RouterExecutionMeta(
                task=task,
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                success=success,
                retry_count=retry_count,
                fallback_used=fallback_used,
                usage_prompt_tokens=usage_prompt,
                usage_completion_tokens=usage_completion,
                usage_total_tokens=usage_total,
            )
        )

    def _log_failure(
        self,
        task: AITask,
        provider_name: str,
        model: str,
        latency_ms: float,
        fallback_used: bool,
        error: str,
    ) -> None:
        self._log_execution(
            RouterExecutionMeta(
                task=task,
                provider=provider_name,
                model=model,
                latency_ms=latency_ms,
                success=False,
                retry_count=0,
                fallback_used=fallback_used,
                error=error,
            )
        )
        logger.warning(
            "AI provider failed for task=%s provider=%s: %s",
            task,
            provider_name,
            error,
        )

    async def _dispatch_generation(
        self,
        task: AITask,
        operation,
    ) -> GenerationResult:
        result = await self._dispatch_single(task, operation)
        if not isinstance(result, GenerationResult):
            raise ProviderError(f"Expected GenerationResult for task {task}")
        return result


def create_ai_router(settings: Settings) -> AITaskRouter:
    return AITaskRouter(settings)
