"""Medical document metadata extraction using an LLM provider."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from pydantic import ValidationError

from app.ai.llm.openai_provider import LLMProviderError
from app.ai.llm.provider import ChatMessage, LLMProvider
from app.ai.prompts.loader import render_prompt
from app.ai.schemas.metadata import ExtractedDocumentMetadata
from app.core.database.enums import DocumentType

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 12_000


@dataclass(frozen=True)
class MetadataExtractionResult:
    metadata: ExtractedDocumentMetadata
    model_name: str


class MetadataExtractionError(Exception):
    """Raised when metadata extraction fails."""


class MetadataExtractor:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def extract(
        self,
        extracted_text: str,
        *,
        document_type: DocumentType,
    ) -> MetadataExtractionResult:
        text = extracted_text.strip()
        if not text:
            raise MetadataExtractionError("Cannot extract metadata from empty document text")

        truncated = text[:MAX_DOCUMENT_CHARS]
        prompt = render_prompt(
            "metadata",
            document_text=truncated,
            document_type=document_type.value,
        )

        try:
            completion = await self._provider.complete(
                [ChatMessage(role="user", content=prompt)],
                temperature=0.0,
                max_tokens=1200,
            )
        except LLMProviderError as exc:
            raise MetadataExtractionError(str(exc)) from exc

        metadata = self._parse_response(completion.content)
        return MetadataExtractionResult(metadata=metadata, model_name=completion.model)

    def _parse_response(self, raw: str) -> ExtractedDocumentMetadata:
        payload = self._extract_json(raw)
        try:
            return ExtractedDocumentMetadata.model_validate(payload)
        except ValidationError as exc:
            raise MetadataExtractionError(
                f"Metadata failed structured validation: {exc}"
            ) from exc

    def _extract_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise MetadataExtractionError(
                f"Metadata response is not valid JSON: {raw[:300]}"
            ) from exc

        if not isinstance(data, dict):
            raise MetadataExtractionError("Metadata JSON must be an object")
        return data
