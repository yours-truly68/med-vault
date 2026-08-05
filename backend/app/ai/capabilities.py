"""Provider capability registry — derived from actual provider implementations."""

from __future__ import annotations

from dataclasses import dataclass

from app.ai.config import AITask


@dataclass(frozen=True)
class ProviderCapabilities:
    supports_chat: bool = False
    supports_embeddings: bool = False
    supports_structured_output: bool = False
    supports_vision: bool = False
    supports_streaming: bool = False
    supports_json_schema: bool = False


def _openai_compatible_capabilities(*, supports_json_mode: bool) -> ProviderCapabilities:
    """Capabilities for OpenAI-compatible HTTP providers (OpenAI, Groq, Vercel, Ollama, xAI)."""
    return ProviderCapabilities(
        supports_chat=True,
        supports_embeddings=True,
        supports_structured_output=True,
        supports_json_schema=supports_json_mode,
        supports_vision=False,
    )


# Implementation truth — each flag reflects what the provider class actually does today.
# vercel/ollama: structured_output() works via prompting only (no response_format json_object).
# OpenAI-compatible providers: vision() always raises ProviderError.
IMPLEMENTED_PROVIDER_CAPABILITIES: dict[str, ProviderCapabilities] = {
    "openai": _openai_compatible_capabilities(supports_json_mode=True),
    "groq": _openai_compatible_capabilities(supports_json_mode=True),
    "vercel": _openai_compatible_capabilities(supports_json_mode=False),
    "ollama": _openai_compatible_capabilities(supports_json_mode=False),
    "xai": ProviderCapabilities(
        supports_chat=True,
        supports_structured_output=True,
        supports_json_schema=True,
        supports_embeddings=False,
        supports_vision=False,
    ),
    "gemini": ProviderCapabilities(
        supports_chat=True,
        supports_embeddings=True,
        supports_structured_output=True,
        supports_vision=True,
        supports_json_schema=True,
    ),
}

REGISTERED_PROVIDERS = frozenset(IMPLEMENTED_PROVIDER_CAPABILITIES.keys())

TASK_REQUIRED_CAPABILITIES: dict[AITask, tuple[str, ...]] = {
    AITask.CLASSIFICATION: ("supports_chat", "supports_structured_output"),
    AITask.METADATA: ("supports_chat", "supports_structured_output"),
    AITask.SUMMARY: ("supports_chat", "supports_structured_output"),
    AITask.CHAT: ("supports_chat",),
    AITask.EMBEDDING: ("supports_embeddings",),
}

METHOD_CAPABILITY_MAP: dict[str, str] = {
    "generate": "supports_chat",
    "structured_output": "supports_structured_output",
    "vision": "supports_vision",
    "embed": "supports_embeddings",
}


def get_provider_capabilities(provider: str) -> ProviderCapabilities | None:
    return IMPLEMENTED_PROVIDER_CAPABILITIES.get(provider.lower().strip())


def provider_supports_task(provider: str, task: AITask) -> bool:
    caps = get_provider_capabilities(provider)
    if caps is None:
        return False
    for attr in TASK_REQUIRED_CAPABILITIES[task]:
        if not getattr(caps, attr, False):
            return False
    return True


def capability_matrix_rows() -> list[dict[str, object]]:
    """Render-ready capability matrix for all registered providers."""
    rows: list[dict[str, object]] = []
    for provider in sorted(REGISTERED_PROVIDERS):
        caps = IMPLEMENTED_PROVIDER_CAPABILITIES[provider]
        rows.append(
            {
                "provider": provider,
                "generate": caps.supports_chat,
                "structured_output": caps.supports_structured_output,
                "json_schema_mode": caps.supports_json_schema,
                "vision": caps.supports_vision,
                "embed": caps.supports_embeddings,
                "streaming": caps.supports_streaming,
            }
        )
    return rows


def find_capability_mismatches(
    advertised: dict[str, ProviderCapabilities] | None = None,
) -> list[str]:
    """Compare advertised capabilities against implementation truth."""
    advertised = advertised or IMPLEMENTED_PROVIDER_CAPABILITIES
    mismatches: list[str] = []

    for provider, declared in advertised.items():
        implemented = IMPLEMENTED_PROVIDER_CAPABILITIES.get(provider)
        if implemented is None:
            mismatches.append(f"{provider}: advertised but not registered in factory")
            continue

        for field in ProviderCapabilities.__dataclass_fields__:
            declared_value = getattr(declared, field)
            implemented_value = getattr(implemented, field)
            if declared_value and not implemented_value:
                mismatches.append(
                    f"{provider}: advertises {field}=True but implementation does not support it"
                )
    return mismatches
