from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database.enums import ProcessingJobStatus, ProcessingStage

if TYPE_CHECKING:
    from app.modules.documents.models import Document


class ProcessingJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        Index("ix_processing_jobs_document_id", "document_id"),
        Index("ix_processing_jobs_status", "status"),
        Index("ix_processing_jobs_stage", "stage"),
    )

    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProcessingStage.UPLOADED.value,
        server_default=ProcessingStage.UPLOADED.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ProcessingJobStatus.PENDING.value,
        server_default=ProcessingJobStatus.PENDING.value,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    document: Mapped[Document] = relationship(back_populates="processing_jobs")


class ProcessingControl(Base):
    """Singleton row for global processing pause/resume."""

    __tablename__ = "processing_control"
    __table_args__ = (UniqueConstraint("singleton_key", name="uq_processing_control_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    singleton_key: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="global",
        server_default="global",
    )
    globally_paused: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
    )
