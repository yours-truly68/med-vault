"""Search service: ranked semantic results with citations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.embeddings.factory import create_embedding_provider
from app.ai.embeddings.pg_vector_store import PgVectorStore
from app.core.config.settings import Settings
from app.core.exceptions import ValidationError
from app.modules.documents.models import Document
from app.modules.search.search import SemanticSearch, SemanticSearchError
from app.modules.search.schemas import (
    SearchCitation,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)
from app.modules.users.models.models import User

EXCERPT_MAX_CHARS = 280


class SearchService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        *,
        semantic_search: SemanticSearch | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        if semantic_search is not None:
            self._search = semantic_search
        else:
            provider = create_embedding_provider(settings)
            store = PgVectorStore(session)
            self._search = SemanticSearch(provider, store)

    async def semantic_search(self, user: User, payload: SearchRequest) -> SearchResponse:
        try:
            result = await self._search.search(
                payload.query,
                user_id=user.id,
                limit=payload.limit,
                min_score=payload.min_score,
                family_member_id=payload.family_member_id,
            )
        except SemanticSearchError as exc:
            raise ValidationError(str(exc)) from exc

        documents = await self._load_documents(
            user.id,
            [hit.document_id for hit in result.hits],
        )

        items: list[SearchResultItem] = []
        citations: list[SearchCitation] = []

        for rank, hit in enumerate(result.hits, start=1):
            document = documents.get(hit.document_id)
            if document is None:
                continue

            citation = self._build_citation(document)
            citations.append(citation)
            items.append(
                SearchResultItem(
                    rank=rank,
                    score=hit.score,
                    document_id=document.id,
                    citation=citation,
                )
            )

        return SearchResponse(
            query=result.query,
            total=len(items),
            results=items,
            citations=citations,
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

    def _build_citation(self, document: Document) -> SearchCitation:
        summary = None
        ai_summary = document.__dict__.get("ai_summary")
        if ai_summary is not None and ai_summary.summary:
            summary = ai_summary.summary

        excerpt_source = summary or document.extracted_text
        excerpt = self._excerpt(excerpt_source)

        return SearchCitation(
            document_id=document.id,
            original_filename=document.original_filename,
            document_type=document.document_type,
            document_date=document.document_date,
            family_member_id=document.family_member_id,
            excerpt=excerpt,
            summary=summary,
        )

    def _excerpt(self, text: str | None) -> str | None:
        if not text:
            return None
        cleaned = " ".join(text.split())
        if len(cleaned) <= EXCERPT_MAX_CHARS:
            return cleaned
        return cleaned[: EXCERPT_MAX_CHARS - 1].rstrip() + "…"
