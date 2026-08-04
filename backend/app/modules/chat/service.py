"""Chat service: retrieve top-K documents and generate a grounded RAG answer."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.embeddings.factory import create_embedding_provider
from app.ai.embeddings.pg_vector_store import PgVectorStore
from app.ai.llm.factory import create_llm_provider
from app.ai.rag import RAGError, RetrievalAugmentedGenerator, RetrievedDocument
from app.core.config.settings import Settings
from app.core.exceptions import ValidationError
from app.modules.chat.schemas import ChatAskRequest, ChatAskResponse, ChatCitation
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

        self._rag = rag or RetrievalAugmentedGenerator(create_llm_provider(settings))

    async def ask(self, user: User, payload: ChatAskRequest) -> ChatAskResponse:
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

            summary = self._summary_text(document)
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
                    score=hit.score,
                    summary=summary,
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
            citations = [
                citation_by_id[doc_id]
                for doc_id in rag_result.cited_document_ids
                if doc_id in citation_by_id
            ]
            # Guarantee citations on every grounded answer.
            if not citations:
                citations = list(citation_by_id.values())

        return ChatAskResponse(
            question=payload.question.strip(),
            answer=rag_result.answer,
            insufficient_context=rag_result.insufficient_context,
            citations=citations,
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
            .options(selectinload(Document.ai_summary))
            .where(
                Document.user_id == user_id,
                Document.id.in_(document_ids),
            )
        )
        return {document.id: document for document in result.scalars().all()}

    def _summary_text(self, document: Document) -> str | None:
        ai_summary = document.__dict__.get("ai_summary")
        if ai_summary is not None and ai_summary.summary:
            return ai_summary.summary
        return None

    def _excerpt(self, text: str | None) -> str | None:
        if not text:
            return None
        cleaned = " ".join(text.split())
        if len(cleaned) <= EXCERPT_MAX_CHARS:
            return cleaned
        return cleaned[: EXCERPT_MAX_CHARS - 1].rstrip() + "…"
