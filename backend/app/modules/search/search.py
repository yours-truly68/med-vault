"""Semantic search over document embeddings."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.ai.embeddings.openai_provider import EmbeddingProviderError
from app.ai.embeddings.provider import EmbeddingProvider
from app.ai.embeddings.vector import SimilarityHit, VectorStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SemanticSearchResult:
    query: str
    hits: list[SimilarityHit]


class SemanticSearchError(Exception):
    """Raised when semantic search fails."""


class SemanticSearch:
    """Natural language → embedding → similarity search."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        store: VectorStore,
    ) -> None:
        self._provider = provider
        self._store = store

    async def search(
        self,
        query: str,
        *,
        user_id: UUID,
        limit: int = 10,
        min_score: float = 0.0,
        family_member_id: UUID | None = None,
    ) -> SemanticSearchResult:
        cleaned = query.strip()
        if not cleaned:
            raise SemanticSearchError("Search query must not be empty")

        try:
            embedding = await self._provider.embed(cleaned)
        except EmbeddingProviderError as exc:
            raise SemanticSearchError(str(exc)) from exc

        hits = await self._store.similarity_search(
            embedding.vector,
            user_id=user_id,
            limit=limit,
            min_score=min_score,
            family_member_id=family_member_id,
        )
        logger.debug(
            "Semantic search for user %s returned %s hits (limit=%s)",
            user_id,
            len(hits),
            limit,
        )
        return SemanticSearchResult(query=cleaned, hits=hits)
