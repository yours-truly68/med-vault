"""Tests for provider capability matrix and implementation truth."""

from __future__ import annotations

import inspect

import pytest

from app.ai.capabilities import (
    IMPLEMENTED_PROVIDER_CAPABILITIES,
    REGISTERED_PROVIDERS,
    capability_matrix_rows,
    find_capability_mismatches,
    provider_supports_task,
)
from app.ai.config import AITask
from app.ai.factory import registered_providers
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openai import OpenAICompatibleProvider
from app.ai.providers.base import ProviderError
from app.ai.validation import validate_provider_capability_matrix


def test_registered_providers_match_capability_registry() -> None:
    from app.ai.factory import _register_defaults

    _register_defaults()
    assert registered_providers() == REGISTERED_PROVIDERS


def test_capability_matrix_has_no_internal_mismatches() -> None:
    validate_provider_capability_matrix()
    assert find_capability_mismatches() == []


def test_vercel_capability_matrix() -> None:
    caps = IMPLEMENTED_PROVIDER_CAPABILITIES["vercel"]
    assert caps.supports_chat is True
    assert caps.supports_embeddings is True
    assert caps.supports_structured_output is True
    assert caps.supports_json_schema is False
    assert caps.supports_vision is False


def test_vercel_does_not_support_vision_task() -> None:
    assert provider_supports_task("vercel", AITask.CHAT) is True
    assert provider_supports_task("vercel", AITask.EMBEDDING) is True


def test_gemini_supports_all_ai_tasks() -> None:
    for task in AITask:
        assert provider_supports_task("gemini", task) is True


def test_xai_does_not_support_embeddings() -> None:
    assert provider_supports_task("xai", AITask.CHAT) is True
    assert provider_supports_task("xai", AITask.EMBEDDING) is False


@pytest.mark.asyncio
async def test_openai_compatible_embed_is_implemented() -> None:
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        base_url="https://example.com/v1",
        label="vercel",
    )
    assert inspect.iscoroutinefunction(provider.embed)
    assert "raise ProviderError" not in inspect.getsource(provider.embed)


def test_capability_matrix_rows_cover_all_providers() -> None:
    rows = capability_matrix_rows()
    assert {row["provider"] for row in rows} == REGISTERED_PROVIDERS
