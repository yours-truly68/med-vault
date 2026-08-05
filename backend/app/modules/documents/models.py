from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database.enums import EMBEDDING_DIMENSIONS, DocumentStatus

if TYPE_CHECKING:
    from app.modules.family_members.models import FamilyMember
    from app.modules.users.models.models import User


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_user_id", "user_id"),
        Index("ix_documents_family_member_id", "family_member_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_document_type", "document_type"),
        Index("ix_documents_document_date", "document_date"),
        Index("ix_documents_user_id_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    family_member_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("family_members.id", ondelete="CASCADE"),
        nullable=False,
    )

    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    bucket: Mapped[str | None] = mapped_column(String(255), nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)

    @property
    def object_key(self) -> str:
        return self.storage_path

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=DocumentStatus.PENDING.value,
        server_default=DocumentStatus.PENDING.value,
    )
    indexing_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="not_started",
        server_default="not_started",
    )
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    indexing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_timings: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    user: Mapped[User] = relationship(back_populates="documents")
    family_member: Mapped[FamilyMember] = relationship(back_populates="documents")
    document_metadata: Mapped[DocumentMetadata | None] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    ai_summary: Mapped[AISummary | None] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )
    embedding: Mapped[Embedding | None] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Document id={self.id} filename={self.original_filename!r} "
            f"status={self.status!r}>"
        )


class DocumentMetadata(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_metadata"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_document_metadata_document_id"),
        Index("ix_document_metadata_hospital_name", "hospital_name"),
        Index("ix_document_metadata_doctor_name", "doctor_name"),
        Index("ix_document_metadata_document_type", "document_type"),
        Index("ix_document_metadata_document_date", "document_date"),
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    doctor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    patient_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    document: Mapped[Document] = relationship(back_populates="document_metadata")

    def __repr__(self) -> str:
        return f"<DocumentMetadata id={self.id} document_id={self.document_id}>"


class AISummary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "ai_summaries"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_ai_summaries_document_id"),
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    document: Mapped[Document] = relationship(back_populates="ai_summary")

    def __repr__(self) -> str:
        return f"<AISummary id={self.id} document_id={self.document_id}>"


class Embedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "embeddings"
    __table_args__ = (
        UniqueConstraint("document_id", name="uq_embeddings_document_id"),
        Index("ix_embeddings_model_name", "model_name"),
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding: Mapped[list[float]] = mapped_column(
        Vector(EMBEDDING_DIMENSIONS),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    dimensions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=EMBEDDING_DIMENSIONS,
        server_default=str(EMBEDDING_DIMENSIONS),
    )

    document: Mapped[Document] = relationship(back_populates="embedding")

    def __repr__(self) -> str:
        return (
            f"<Embedding id={self.id} document_id={self.document_id} "
            f"model_name={self.model_name!r}>"
        )
