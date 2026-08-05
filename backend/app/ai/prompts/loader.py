"""Load prompt templates from app/ai/prompts/."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
_PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}")


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file is missing."""


class UnresolvedPromptPlaceholderError(ValueError):
    """Raised when a template still contains unreplaced placeholders."""


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt file by name (with or without .md extension)."""
    filename = name if name.endswith(".md") else f"{name}.md"
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise PromptNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **variables: str) -> str:
    """Load a prompt, replace ``{{key}}`` placeholders, and validate completeness."""
    template = load_prompt(name)
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)

    unresolved = sorted(set(_PLACEHOLDER_PATTERN.findall(rendered)))
    if unresolved:
        raise UnresolvedPromptPlaceholderError(
            f"Prompt '{name}' has unresolved placeholders: {', '.join(unresolved)}"
        )
    return rendered
