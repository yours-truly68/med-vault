from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.database.enums import DocumentType


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)
    min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    family_member_id: UUID | None = None


class SearchCitation(BaseModel):
    document_id: UUID
    original_filename: str
    document_type: DocumentType | None = None
    document_date: date | None = None
    family_member_id: UUID
    excerpt: str | None = None
    summary: str | None = None


class SearchResultItem(BaseModel):
    rank: int
    score: float
    document_id: UUID
    citation: SearchCitation


class SearchResponse(BaseModel):
    query: str
    total: int = Field(ge=0)
    results: list[SearchResultItem]
    citations: list[SearchCitation]
