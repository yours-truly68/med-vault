"""Factory for LLM providers — routes through AITaskRouter for backward compatibility."""

from __future__ import annotations

from app.ai.adapters import create_task_llm_provider
from app.ai.config import AITask
from app.ai.llm.provider import LLMProvider
from app.ai.router import create_ai_router
from app.core.config.settings import Settings


def create_llm_provider(settings: Settings, *, task: AITask = AITask.CHAT) -> LLMProvider:
    """Create an LLMProvider backed by the task router (defaults to chat/RAG task)."""
    router = create_ai_router(settings)
    return create_task_llm_provider(router, task)
