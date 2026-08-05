"""Add rate-limit retry fields to processing jobs."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e8a3c5d91f42"
down_revision: str | None = "d7e1f4a82b60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "processing_jobs",
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "processing_jobs",
        sa.Column("wait_reason", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_processing_jobs_next_retry_at",
        "processing_jobs",
        ["next_retry_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_next_retry_at", table_name="processing_jobs")
    op.drop_column("processing_jobs", "wait_reason")
    op.drop_column("processing_jobs", "next_retry_at")
