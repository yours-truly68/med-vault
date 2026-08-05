"""Backward-compatible alias for OpenAICompatibleChatProvider."""

from app.ai.llm.compatible_chat import OpenAICompatibleChatProvider
from app.ai.llm.errors import LLMProviderError

OpenAIProvider = OpenAICompatibleChatProvider

__all__ = ["LLMProviderError", "OpenAIProvider"]
