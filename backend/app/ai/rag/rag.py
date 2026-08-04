"""Retrieval-augmented generation: context construction and grounded answers."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from uuid import UUID

from pydantic import ValidationError

from app.ai.llm.openai_provider import LLMProviderError
from app.ai.llm.provider import ChatMessage, LLMProvider
from app.ai.prompts.loader import render_prompt
from app.ai.schemas.rag import GroundedAnswer

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = (
    "I could not find relevant information in your uploaded medical documents "
    "to answer that question."
)
MAX_DOC_CHARS = 4_000


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: UUID
    original_filename: str
    document_type: str | None
    document_date: str | None
    score: float
    summary: str | None
    extracted_text: str | None


@dataclass(frozen=True)
class RAGResult:
    answer: str
    cited_document_ids: list[UUID]
    insufficient_context: bool
    model_name: str | None
    retrieved_document_ids: list[UUID]


class RAGError(Exception):
    """Raised when RAG generation fails."""


class RetrievalAugmentedGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def build_context(self, documents: list[RetrievedDocument]) -> str:
        if not documents:
            return ""

        blocks: list[str] = []
        for index, document in enumerate(documents, start=1):
            body = (document.summary or document.extracted_text or "").strip()
            if not body:
                body = "(No extracted text available.)"
            body = body[:MAX_DOC_CHARS]
            blocks.append(
                "\n".join(
                    [
                        f"[Document {index}]",
                        f"document_id: {document.document_id}",
                        f"filename: {document.original_filename}",
                        f"type: {document.document_type or 'unknown'}",
                        f"date: {document.document_date or 'unknown'}",
                        f"similarity_score: {document.score:.4f}",
                        "content:",
                        body,
                    ]
                )
            )
        return "\n\n".join(blocks)

    async def generate(
        self,
        question: str,
        documents: list[RetrievedDocument],
    ) -> RAGResult:
        cleaned_question = question.strip()
        if not cleaned_question:
            raise RAGError("Question must not be empty")

        retrieved_ids = [document.document_id for document in documents]
        if not documents:
            return RAGResult(
                answer=NO_CONTEXT_ANSWER,
                cited_document_ids=[],
                insufficient_context=True,
                model_name=None,
                retrieved_document_ids=[],
            )

        context = self.build_context(documents)
        prompt = render_prompt(
            "rag",
            question=cleaned_question,
            context=context,
        )

        try:
            completion = await self._provider.complete(
                [ChatMessage(role="user", content=prompt)],
                temperature=0.0,
                max_tokens=1600,
            )
        except LLMProviderError as exc:
            raise RAGError(str(exc)) from exc

        grounded = self._parse_response(completion.content)
        allowed = set(retrieved_ids)
        cited = [doc_id for doc_id in grounded.cited_document_ids if doc_id in allowed]

        # Every grounded answer must cite sources when context was used.
        if not grounded.insufficient_context and not cited:
            cited = retrieved_ids

        if grounded.insufficient_context:
            cited = []

        return RAGResult(
            answer=grounded.answer,
            cited_document_ids=cited,
            insufficient_context=grounded.insufficient_context,
            model_name=completion.model,
            retrieved_document_ids=retrieved_ids,
        )

    def _parse_response(self, raw: str) -> GroundedAnswer:
        payload = self._extract_json(raw)
        try:
            return GroundedAnswer.model_validate(payload)
        except ValidationError as exc:
            raise RAGError(f"RAG response failed structured validation: {exc}") from exc

    def _extract_json(self, raw: str) -> dict:
        cleaned = raw.strip()
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        if fence:
            cleaned = fence.group(1).strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RAGError(f"RAG response is not valid JSON: {raw[:300]}") from exc

        if not isinstance(data, dict):
            raise RAGError("RAG JSON must be an object")
        return data
