"""Load prompt templates from app/ai/prompts/."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt template file is missing."""


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load a prompt file by name (with or without .md extension)."""
    filename = name if name.endswith(".md") else f"{name}.md"
    path = PROMPTS_DIR / filename
    if not path.is_file():
        raise PromptNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(name: str, **variables: str) -> str:
    """Load a prompt and replace ``{{key}}`` placeholders."""
    template = load_prompt(name)
    rendered = template
    for key, value in variables.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered
