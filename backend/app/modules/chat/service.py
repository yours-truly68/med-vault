"""Chat service: retrieve top-K documents and generate a grounded RAG answer."""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator
from uuid import UUID

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.embeddings.factory import create_embedding_provider
from app.ai.embeddings.pg_vector_store import PgVectorStore
from app.ai.router import create_ai_router
from app.ai.rag import RAGError, RetrievalAugmentedGenerator, RetrievedDocument
from app.core.config.settings import Settings
from app.core.exceptions import ValidationError
from app.modules.chat.schemas import (
    ChatAskRequest,
    ChatAskResponse,
    ChatCitation,
    ChatSupportingDetails,
    ChatTimelineEntry,
)
from app.modules.documents.models import Document
from app.modules.search.search import SemanticSearch, SemanticSearchError
from app.modules.users.models.models import User

EXCERPT_MAX_CHARS = 280


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        semantic_search: SemanticSearch | None = None,
        rag: RetrievalAugmentedGenerator | None = None,
    ) -> None:
        self._session = session
        self._settings = settings

        if semantic_search is not None:
            self._search = semantic_search
        else:
            self._search = SemanticSearch(
                create_embedding_provider(settings),
                PgVectorStore(session),
            )

        self._rag = rag or RetrievalAugmentedGenerator(create_ai_router(settings))

    async def stream_ask(
        self,
        user: User,
        payload: ChatAskRequest,
        *,
        request: Request | None = None,
    ) -> AsyncGenerator[str, None]:
        import json
        import time

        start_time = time.perf_counter()
        yield f"event: start\ndata: {json.dumps({'question': payload.question.strip()})}\n\n"
        yield f"event: thinking\ndata: {json.dumps({'stage': 'searching'})}\n\n"

        if request is not None and await request.is_disconnected():
            yield f"event: error\ndata: {json.dumps({'detail': 'Client disconnected'})}\n\n"
            return

        top_k = payload.top_k or self._settings.rag_top_k
        min_score = (
            self._settings.rag_min_score
            if payload.min_score is None
            else payload.min_score
        )

        try:
            search_result = await self._search.search(
                payload.question,
                user_id=user.id,
                limit=top_k,
                min_score=min_score,
                family_member_id=payload.family_member_id,
            )
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            return

        documents = await self._load_documents(
            user.id,
            [hit.document_id for hit in search_result.hits],
        )

        retrieved: list[RetrievedDocument] = []
        citations: list[dict] = []

        for hit in search_result.hits:
            doc = documents.get(hit.document_id)
            if not doc:
                continue
            meta = doc.__dict__.get("document_metadata")
            ai_sum = doc.__dict__.get("ai_summary")

            retrieved.append(
                RetrievedDocument(
                    document_id=doc.id,
                    original_filename=doc.original_filename,
                    document_type=doc.document_type,
                    document_date=doc.document_date.isoformat() if doc.document_date else None,
                    page_count=doc.page_count,
                    score=hit.score,
                    summary=ai_sum.summary if ai_sum else None,
                    diagnosis=meta.diagnosis if meta else None,
                    extracted_text=doc.extracted_text,
                )
            )
            citations.append({
                "document_id": str(doc.id),
                "original_filename": doc.original_filename,
                "document_type": doc.document_type,
                "document_date": doc.document_date.isoformat() if doc.document_date else None,
                "family_member_id": str(doc.family_member_id),
                "score": hit.score,
                "excerpt": self._excerpt(ai_sum.summary if ai_sum else doc.extracted_text),
            })

        yield f"event: thinking\ndata: {json.dumps({'stage': 'generating'})}\n\n"

        ttft_logged = False
        ttft_ms = 0
        try:
            async for token in self._rag.stream_generate(payload.question, retrieved):
                if request is not None and await request.is_disconnected():
                    break
                if not ttft_logged:
                    ttft_ms = int((time.perf_counter() - start_time) * 1000)
                    ttft_logged = True
                yield f"event: token\ndata: {json.dumps({'delta': token})}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            return

        yield f"event: metadata\ndata: {json.dumps({'citations': citations})}\n\n"
        total_time_ms = int((time.perf_counter() - start_time) * 1000)
        yield f"event: done\ndata: {json.dumps({'ttft_ms': ttft_ms, 'total_ms': total_time_ms})}\n\n"

    async def ask(
        self,
        user: User,
        payload: ChatAskRequest,
        *,
        request: Request | None = None,
    ) -> ChatAskResponse:
        if request is not None and await request.is_disconnected():
            raise asyncio.CancelledError("Client disconnected before search execution")

        top_k = payload.top_k or self._settings.rag_top_k
        min_score = (
            self._settings.rag_min_score
            if payload.min_score is None
            else payload.min_score
        )

        try:
            search_result = await self._search.search(
                payload.question,
                user_id=user.id,
                limit=top_k,
                min_score=min_score,
                family_member_id=payload.family_member_id,
            )
        except SemanticSearchError as exc:
            raise ValidationError(str(exc)) from exc

        if not search_result.hits:
            # Check if user has READY documents that are currently being indexed
            query = select(Document).where(
                Document.user_id == user.id,
                Document.status == "ready",
                Document.indexing_status != "indexed",
            )
            if payload.family_member_id is not None:
                query = query.where(Document.family_member_id == payload.family_member_id)
            res = await self._session.execute(query)
            unindexed_docs = res.scalars().all()
            if unindexed_docs:
                return ChatAskResponse(
                    question=payload.question.strip(),
                    answer="Your document has been processed successfully! The AI search index is currently being prepared in the background. Full search will become available shortly.",
                    insufficient_context=True,
                    citations=[],
                )

        documents = await self._load_documents(
            user.id,
            [hit.document_id for hit in search_result.hits],
        )

        retrieved: list[RetrievedDocument] = []
        citation_by_id: dict[UUID, ChatCitation] = {}

        for hit in search_result.hits:
            document = documents.get(hit.document_id)
            if document is None:
                continue

            metadata = document.__dict__.get("document_metadata")
            ai_summary = document.__dict__.get("ai_summary")
            summary = ai_summary.summary if ai_summary is not None else None
            highlights = list(ai_summary.highlights or []) if ai_summary else []
            key_findings: list[str] = []
            if ai_summary and ai_summary.key_findings:
                try:
                    import json

                    payload_json = json.loads(ai_summary.key_findings)
                    if isinstance(payload_json, list):
                        key_findings = [str(item) for item in payload_json]
                    elif isinstance(payload_json, dict):
                        key_findings = [
                            str(item)
                            for item in (payload_json.get("findings") or [])
                        ]
                except json.JSONDecodeError:
                    key_findings = [
                        line.strip()
                        for line in ai_summary.key_findings.splitlines()
                        if line.strip()
                    ]

            medicines = list(metadata.medicines or []) if metadata else []
            lab_measurements = [
                {
                    "test_name": row.test_name,
                    "value": float(row.value),
                    "unit": row.unit,
                    "reference_low": (
                        float(row.reference_low)
                        if row.reference_low is not None
                        else None
                    ),
                    "reference_high": (
                        float(row.reference_high)
                        if row.reference_high is not None
                        else None
                    ),
                }
                for row in (document.__dict__.get("lab_measurements") or [])
            ]

            retrieved.append(
                RetrievedDocument(
                    document_id=document.id,
                    original_filename=document.original_filename,
                    document_type=document.document_type,
                    document_date=(
                        document.document_date.isoformat()
                        if document.document_date is not None
                        else None
                    ),
                    page_count=document.page_count,
                    score=hit.score,
                    summary=summary,
                    highlights=highlights,
                    key_findings=key_findings,
                    patient_name=metadata.patient_name if metadata else None,
                    doctor_name=metadata.doctor_name if metadata else None,
                    hospital_name=metadata.hospital_name if metadata else None,
                    diagnosis=metadata.diagnosis if metadata else None,
                    medicines=medicines,
                    lab_measurements=lab_measurements,
                    procedures=list(metadata.procedures or []) if metadata else [],
                    allergies=list(metadata.allergies or []) if metadata else [],
                    vaccinations=list(metadata.vaccinations or []) if metadata else [],
                    medical_devices=list(metadata.medical_devices or []) if metadata else [],
                    follow_up=metadata.follow_up if metadata else None,
                    admission_date=(
                        metadata.admission_date.isoformat()
                        if metadata and metadata.admission_date
                        else None
                    ),
                    discharge_date=(
                        metadata.discharge_date.isoformat()
                        if metadata and metadata.discharge_date
                        else None
                    ),
                    extracted_text=document.extracted_text,
                )
            )
            citation_by_id[document.id] = ChatCitation(
                document_id=document.id,
                original_filename=document.original_filename,
                document_type=document.document_type,
                document_date=document.document_date,
                family_member_id=document.family_member_id,
                score=hit.score,
                excerpt=self._excerpt(summary or document.extracted_text),
                summary=summary,
            )

        try:
            rag_result = await self._rag.generate(payload.question, retrieved)
        except RAGError as exc:
            raise ValidationError(str(exc)) from exc

        if rag_result.insufficient_context:
            citations: list[ChatCitation] = []
        else:
            citations = []
            for citation in rag_result.citations:
                doc_id = UUID(str(citation["document_id"]))
                base = citation_by_id.get(doc_id)
                if base is None:
                    continue
                citations.append(
                    ChatCitation(
                        document_id=base.document_id,
                        original_filename=base.original_filename,
                        document_type=base.document_type,
                        document_date=base.document_date,
                        family_member_id=base.family_member_id,
                        score=base.score,
                        page=citation.get("page"),
                        excerpt=base.excerpt,
                        summary=base.summary,
                    )
                )
            if not citations:
                citations = [
                    citation_by_id[doc_id]
                    for doc_id in rag_result.cited_document_ids
                    if doc_id in citation_by_id
                ]

        supporting = None
        if rag_result.supporting_details:
            supporting = ChatSupportingDetails.model_validate(rag_result.supporting_details)

        timeline = [
            ChatTimelineEntry.model_validate(entry) for entry in rag_result.timeline
        ]

        return ChatAskResponse(
            question=payload.question.strip(),
            answer=rag_result.answer,
            insufficient_context=rag_result.insufficient_context,
            citations=citations,
            supporting_details=supporting,
            timeline=timeline,
            model_name=rag_result.model_name,
        )

    async def _load_documents(
        self,
        user_id: UUID,
        document_ids: list[UUID],
    ) -> dict[UUID, Document]:
        if not document_ids:
            return {}

        result = await self._session.execute(
            select(Document)
            .options(
                selectinload(Document.ai_summary),
                selectinload(Document.document_metadata),
                selectinload(Document.lab_measurements),
            )
            .where(
                Document.user_id == user_id,
                Document.id.in_(document_ids),
            )
        )
        return {document.id: document for document in result.scalars().all()}

    def _excerpt(self, text: str | None) -> str | None:
        if not text:
            return None
        cleaned = " ".join(text.split())
        if len(cleaned) <= EXCERPT_MAX_CHARS:
            return cleaned
        return cleaned[: EXCERPT_MAX_CHARS - 1].rstrip() + "…"
