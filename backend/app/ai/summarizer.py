"""Medical document summarization using an LLM provider."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.llm.errors import LLMProviderError
from app.ai.llm.provider import ChatMessage, LLMProvider
from app.ai.prompts.loader import render_prompt
from app.ai.schemas.summary import DocumentSummary
from app.ai.text_compact import compact_document_text
from app.core.database.enums import DocumentType

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 12_000


@dataclass(frozen=True)
class SummarizationResult:
    summary: DocumentSummary
    model_name: str


class SummarizationError(Exception):
    """Raised when document summarization fails."""


class DocumentSummarizer:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def summarize(
        self,
        extracted_text: str,
        *,
        document_type: DocumentType,
    ) -> SummarizationResult:
        text = extracted_text.strip()
        if not text:
            raise SummarizationError("Cannot summarize empty document text")

        truncated = compact_document_text(text, max_chars=MAX_DOCUMENT_CHARS)
        prompt = render_prompt(
            "summarize",
            document_text=truncated,
            document_type=document_type.value,
        )

        try:
            completion = await self._provider.complete(
                [ChatMessage(role="user", content=prompt)],
                temperature=0.0,
                max_tokens=1400,
            )
        except LLMProviderError as exc:
            raise SummarizationError(str(exc)) from exc

        summary = self._parse_response(completion.content)
        return SummarizationResult(summary=summary, model_name=completion.model)

    def _parse_response(self, raw: str) -> DocumentSummary:
        payload = self._extract_json(raw)
        try:
            return DocumentSummary.model_validate(payload)
        except ValidationError as exc:
            raise SummarizationError(
                f"Summary failed structured validation: {exc}"
            ) from exc

    def _extract_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise SummarizationError(
                f"Summary response is not valid JSON: {raw[:300]}"
            ) from exc

        if not isinstance(data, dict):
            raise SummarizationError("Summary JSON must be an object")
        return data
