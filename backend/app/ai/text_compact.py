"""Compact document text before sending to LLM providers.

We do not gzip JSON request bodies — OpenAI-compatible APIs do not accept them.
Instead we reduce token volume by normalizing whitespace before truncation.
"""

from __future__ import annotations

import re


def compact_document_text(text: str, *, max_chars: int) -> str:
    """Collapse redundant whitespace to shrink prompts without losing structure."""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[ \t]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = normalized.strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].strip()
