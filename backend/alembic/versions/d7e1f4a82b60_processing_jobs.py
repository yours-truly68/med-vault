"""Alembic migration: processing jobs and document pipeline fields."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d7e1f4a82b60"
down_revision: str | None = "c4f8a2b91d3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "processing_status",
            sa.String(length=32),
            nullable=False,
            server_default="uploaded",
        ),
    )
    op.add_column(
        "documents",
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documents_processing_status", "documents", ["processing_status"])

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False, server_default="uploaded"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processing_jobs_document_id", "processing_jobs", ["document_id"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])
    op.create_index("ix_processing_jobs_stage", "processing_jobs", ["stage"])

    op.create_table(
        "processing_control",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("singleton_key", sa.String(length=16), nullable=False, server_default="global"),
        sa.Column("globally_paused", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("singleton_key", name="uq_processing_control_singleton"),
    )

    op.execute(
        sa.text(
            "UPDATE documents SET uploaded_at = created_at "
            "WHERE uploaded_at IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_table("processing_control")
    op.drop_index("ix_processing_jobs_stage", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_status", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_document_id", table_name="processing_jobs")
    op.drop_table("processing_jobs")
    op.drop_index("ix_documents_processing_status", table_name="documents")
    op.drop_column("documents", "processed_at")
    op.drop_column("documents", "uploaded_at")
    op.drop_column("documents", "processing_status")
