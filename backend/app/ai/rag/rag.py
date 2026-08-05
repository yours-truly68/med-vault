"""Retrieval-augmented generation: context construction and grounded answers."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from uuid import UUID

from pydantic import ValidationError

from app.ai.llm.errors import LLMProviderError
from app.ai.llm.provider import ChatMessage, LLMProvider
from app.ai.prompts.loader import render_prompt
from app.ai.schemas.rag import GroundedAnswer, RagCitation

logger = logging.getLogger(__name__)

NO_CONTEXT_ANSWER = (
    "I could not find enough information in your uploaded medical documents "
    "to answer that question."
)
MAX_OCR_CHARS = 3_000


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: UUID
    original_filename: str
    document_type: str | None
    document_date: str | None
    page_count: int | None
    score: float
    summary: str | None
    highlights: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    patient_name: str | None = None
    doctor_name: str | None = None
    hospital_name: str | None = None
    diagnosis: str | None = None
    medicines: list[dict] = field(default_factory=list)
    lab_measurements: list[dict] = field(default_factory=list)
    procedures: list[str] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    vaccinations: list[str] = field(default_factory=list)
    medical_devices: list[str] = field(default_factory=list)
    follow_up: str | None = None
    admission_date: str | None = None
    discharge_date: str | None = None
    extracted_text: str | None = None


@dataclass(frozen=True)
class RAGResult:
    answer: str
    cited_document_ids: list[UUID]
    insufficient_context: bool
    model_name: str | None
    retrieved_document_ids: list[UUID]
    supporting_details: dict | None = None
    timeline: list[dict] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)


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
            ocr_excerpt = (document.extracted_text or "").strip()
            if len(ocr_excerpt) > MAX_OCR_CHARS:
                ocr_excerpt = ocr_excerpt[: MAX_OCR_CHARS - 1] + "…"

            structured = {
                "document_id": str(document.document_id),
                "filename": document.original_filename,
                "type": document.document_type or "unknown",
                "date": document.document_date or "unknown",
                "page_count": document.page_count,
                "similarity_score": round(document.score, 4),
                "summary": document.summary,
                "highlights": document.highlights,
                "key_findings": document.key_findings,
                "metadata": {
                    "patient": document.patient_name,
                    "doctor": document.doctor_name,
                    "hospital": document.hospital_name,
                    "diagnosis": document.diagnosis,
                    "medicines": document.medicines,
                    "lab_measurements": document.lab_measurements,
                    "procedures": document.procedures,
                    "allergies": document.allergies,
                    "vaccinations": document.vaccinations,
                    "medical_devices": document.medical_devices,
                    "follow_up": document.follow_up,
                    "admission_date": document.admission_date,
                    "discharge_date": document.discharge_date,
                },
                "extracted_text_excerpt": ocr_excerpt or None,
            }
            blocks.append(
                "\n".join(
                    [
                        f"[Document {index}]",
                        json.dumps(structured, indent=2, ensure_ascii=True),
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
                max_tokens=2200,
            )
        except LLMProviderError as exc:
            raise RAGError(str(exc)) from exc

        grounded = self._parse_response(completion.content)
        allowed = set(retrieved_ids)

        citations: list[RagCitation] = []
        for item in grounded.citations:
            if item.document_id in allowed:
                citations.append(item)

        cited = [item.document_id for item in citations]
        if not cited:
            cited = [
                doc_id
                for doc_id in grounded.cited_document_ids
                if doc_id in allowed
            ]

        if not grounded.insufficient_context and not cited:
            cited = retrieved_ids

        if grounded.insufficient_context:
            cited = []

        supporting = (
            grounded.supporting_details.model_dump()
            if grounded.supporting_details is not None
            else None
        )
        timeline = [entry.model_dump() for entry in grounded.timeline]

        return RAGResult(
            answer=grounded.answer,
            cited_document_ids=cited,
            insufficient_context=grounded.insufficient_context,
            model_name=completion.model,
            retrieved_document_ids=retrieved_ids,
            supporting_details=supporting,
            timeline=timeline,
            citations=[item.model_dump(mode="json") for item in citations],
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
