"""Medical document classification using an LLM provider."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from app.ai.llm.openai_provider import LLMProviderError
from app.ai.llm.provider import ChatMessage, LLMProvider
from app.ai.prompts.loader import render_prompt
from app.core.database.enums import DocumentType

logger = logging.getLogger(__name__)

MAX_DOCUMENT_CHARS = 12_000
VALID_CATEGORIES = frozenset(item.value for item in DocumentType)


@dataclass(frozen=True)
class ClassificationResult:
    category: DocumentType
    confidence: float
    reasoning: str
    model_name: str


class ClassificationError(Exception):
    """Raised when classification fails."""


class DocumentClassifier:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    async def classify(self, extracted_text: str) -> ClassificationResult:
        text = extracted_text.strip()
        if not text:
            raise ClassificationError("Cannot classify empty document text")

        truncated = text[:MAX_DOCUMENT_CHARS]
        prompt = render_prompt("classify", document_text=truncated)

        try:
            completion = await self._provider.complete(
                [ChatMessage(role="user", content=prompt)],
                temperature=0.0,
                max_tokens=400,
            )
        except LLMProviderError as exc:
            raise ClassificationError(str(exc)) from exc

        return self._parse_response(completion.content, completion.model)

    def _parse_response(self, raw: str, model_name: str) -> ClassificationResult:
        payload = self._extract_json(raw)

        try:
            category_raw = str(payload["category"]).strip().lower()
            confidence = float(payload["confidence"])
            reasoning = str(payload["reasoning"]).strip()
        except (KeyError, TypeError, ValueError) as exc:
            raise ClassificationError(
                f"Invalid classification payload: {raw[:300]}"
            ) from exc

        # Accept common aliases from the model.
        aliases = {
            "blood_report": DocumentType.LAB_REPORT.value,
            "lab": DocumentType.LAB_REPORT.value,
            "rx": DocumentType.PRESCRIPTION.value,
            "non_medical": DocumentType.UNRELATED.value,
            "non-medical": DocumentType.UNRELATED.value,
            "irrelevant": DocumentType.UNRELATED.value,
            "reject": DocumentType.UNRELATED.value,
            "rejected": DocumentType.UNRELATED.value,
        }
        category_value = aliases.get(category_raw, category_raw)

        if category_value not in VALID_CATEGORIES:
            raise ClassificationError(f"Unknown category: {category_raw}")

        if not 0.0 <= confidence <= 1.0:
            confidence = max(0.0, min(1.0, confidence))

        if not reasoning:
            reasoning = "No reasoning provided by the model."

        return ClassificationResult(
            category=DocumentType(category_value),
            confidence=round(confidence, 4),
            reasoning=reasoning[:2000],
            model_name=model_name,
        )

    def _extract_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ClassificationError(
                f"Classification response is not valid JSON: {raw[:300]}"
            ) from exc

        if not isinstance(data, dict):
            raise ClassificationError("Classification JSON must be an object")
        return data
