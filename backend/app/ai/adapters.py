"""Adapters bridging the AI router to legacy provider protocols."""

from __future__ import annotations

from typing import Sequence

from app.ai.config import AITask
from app.ai.errors import RateLimitError, is_rate_limit_message
from app.ai.llm.errors import LLMProviderError
from app.ai.llm.provider import ChatCompletion, ChatMessage as LegacyChatMessage, LLMProvider
from app.ai.providers.base import ChatMessage, ProviderError, TransientProviderError
from app.ai.router import AITaskRouter


def _to_router_messages(messages: Sequence[LegacyChatMessage]) -> list[ChatMessage]:
    return [ChatMessage(role=m.role, content=m.content) for m in messages]


def _map_provider_error(exc: ProviderError, *, provider_label: str) -> Exception:
    if isinstance(exc, TransientProviderError) or is_rate_limit_message(str(exc)):
        return RateLimitError(
            str(exc),
            retry_after_seconds=(
                exc.retry_after_seconds if isinstance(exc, TransientProviderError) else None
            ),
            provider_label=provider_label,
        )
    return exc


class RouterLLMProvider:
    """LLMProvider implementation that dispatches through AITaskRouter."""

    def __init__(self, router: AITaskRouter, task: AITask) -> None:
        self._router = router
        self._task = task

    async def complete(
        self,
        messages: list[LegacyChatMessage],
        *,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> ChatCompletion:
        router_messages = _to_router_messages(messages)
        try:
            result = await self._router.structured_output(
                self._task,
                router_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except ProviderError as exc:
            mapped = _map_provider_error(exc, provider_label=self._task.value)
            if isinstance(mapped, RateLimitError):
                raise mapped
            raise LLMProviderError(str(exc)) from exc

        return ChatCompletion(content=result.content, model=result.model)


def create_task_llm_provider(router: AITaskRouter, task: AITask) -> LLMProvider:
    return RouterLLMProvider(router, task)
