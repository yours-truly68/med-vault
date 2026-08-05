"""Medical document summarization using an LLM provider."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.config import AITask
from app.ai.prompts.loader import render_prompt
from app.ai.providers.base import ChatMessage, ProviderError
from app.ai.router import AITaskRouter
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
    def __init__(self, router: AITaskRouter) -> None:
        self._router = router

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

        messages = [ChatMessage(role="user", content=prompt)]

        # Attempt 1
        try:
            completion = await self._router.structured_output(
                AITask.SUMMARY,
                messages,
                temperature=0.0,
                max_tokens=2000,
            )
            summary = self._parse_response(completion.content)
            logger.info(
                "Summarization succeeded on attempt 1: model=%s response_len=%d finish_reason=%s",
                completion.model,
                len(completion.content),
                completion.finish_reason,
            )
            return SummarizationResult(summary=summary, model_name=completion.model)
        except (SummarizationError, ProviderError) as exc:
            logger.warning(
                "Summarization parsing/validation failed on attempt 1: %s. Retrying once...",
                exc,
            )

        # Retry (Attempt 2) with explicit clarification prompt per Task 3 & 5
        retry_instruction = (
            "The previous response contained invalid or truncated JSON. "
            "Return ONLY valid JSON matching the exact schema requested. "
            "Do not include any explanation or commentary."
        )
        retry_messages = [
            ChatMessage(role="user", content=prompt),
            ChatMessage(role="assistant", content=completion.content if 'completion' in locals() else ""),
            ChatMessage(role="user", content=retry_instruction),
        ]

        try:
            completion = await self._router.structured_output(
                AITask.SUMMARY,
                retry_messages,
                temperature=0.0,
                max_tokens=2000,
            )
            summary = self._parse_response(completion.content)
            logger.info(
                "Summarization succeeded on retry attempt 2: model=%s response_len=%d finish_reason=%s",
                completion.model,
                len(completion.content),
                completion.finish_reason,
            )
            return SummarizationResult(summary=summary, model_name=completion.model)
        except (SummarizationError, ProviderError) as exc:
            logger.error("Summarization failed after retry: %s", exc)
            raise SummarizationError(f"Summary failed structured parsing after retry: {exc}") from exc

    def _parse_response(self, raw: str) -> DocumentSummary:
        payload = self._extract_json(raw)
        try:
            return DocumentSummary.model_validate(payload)
        except ValidationError as exc:
            logger.warning("Summary payload failed Pydantic validation: %s", exc)
            raise SummarizationError(
                f"Summary failed structured validation: {exc}"
            ) from exc

    def _extract_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()

        # Sanitize common trailing comma issues before parsing
        cleaned_json = re.sub(r",\s*([\]}])", r"\1", cleaned)

        try:
            data = json.loads(cleaned_json)
        except json.JSONDecodeError as exc:
            raise SummarizationError(
                f"Summary response is not valid JSON: {raw[:300]}"
            ) from exc

        if not isinstance(data, dict):
            raise SummarizationError("Summary JSON must be an object")
        return data
