"""ai_layer_v2

Revision ID: c4f8a2b91d3e
Revises: 2b8511021ee1
Create Date: 2026-08-05 02:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4f8a2b91d3e"
down_revision: Union[str, None] = "2b8511021ee1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))

    op.add_column(
        "document_metadata",
        sa.Column("specialization", sa.String(length=255), nullable=True),
    )
    op.add_column("document_metadata", sa.Column("diagnosis", sa.Text(), nullable=True))
    op.add_column(
        "document_metadata",
        sa.Column("clinical_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "document_metadata",
        sa.Column("admission_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "document_metadata",
        sa.Column("discharge_date", sa.Date(), nullable=True),
    )
    op.add_column("document_metadata", sa.Column("follow_up", sa.Text(), nullable=True))
    op.add_column(
        "document_metadata",
        sa.Column(
            "medicines",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "document_metadata",
        sa.Column(
            "procedures",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "document_metadata",
        sa.Column(
            "allergies",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "document_metadata",
        sa.Column(
            "medical_devices",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "document_metadata",
        sa.Column(
            "vaccinations",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_document_metadata_admission_date",
        "document_metadata",
        ["admission_date"],
        unique=False,
    )
    op.create_index(
        "ix_document_metadata_discharge_date",
        "document_metadata",
        ["discharge_date"],
        unique=False,
    )

    op.add_column(
        "ai_summaries",
        sa.Column(
            "important_dates",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    op.add_column(
        "ai_summaries",
        sa.Column(
            "highlights",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )

    op.create_table(
        "lab_measurements",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_member_id", sa.Uuid(), nullable=False),
        sa.Column("test_name", sa.String(length=255), nullable=False),
        sa.Column("value", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=True),
        sa.Column("reference_low", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("reference_high", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("measured_at", sa.Date(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["family_member_id"], ["family_members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_lab_measurements_document_id",
        "lab_measurements",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_lab_measurements_family_member_test",
        "lab_measurements",
        ["family_member_id", "test_name"],
        unique=False,
    )
    op.create_index(
        "ix_lab_measurements_user_measured_at",
        "lab_measurements",
        ["user_id", "measured_at"],
        unique=False,
    )

    op.create_table(
        "timeline_events",
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("family_member_id", sa.Uuid(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_field", sa.String(length=128), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["family_member_id"], ["family_members.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_timeline_events_document_id",
        "timeline_events",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_timeline_events_user_family_date",
        "timeline_events",
        ["user_id", "family_member_id", "event_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_timeline_events_user_family_date", table_name="timeline_events")
    op.drop_index("ix_timeline_events_document_id", table_name="timeline_events")
    op.drop_table("timeline_events")

    op.drop_index("ix_lab_measurements_user_measured_at", table_name="lab_measurements")
    op.drop_index("ix_lab_measurements_family_member_test", table_name="lab_measurements")
    op.drop_index("ix_lab_measurements_document_id", table_name="lab_measurements")
    op.drop_table("lab_measurements")

    op.drop_column("ai_summaries", "highlights")
    op.drop_column("ai_summaries", "important_dates")

    op.drop_index("ix_document_metadata_discharge_date", table_name="document_metadata")
    op.drop_index("ix_document_metadata_admission_date", table_name="document_metadata")
    op.drop_column("document_metadata", "vaccinations")
    op.drop_column("document_metadata", "medical_devices")
    op.drop_column("document_metadata", "allergies")
    op.drop_column("document_metadata", "procedures")
    op.drop_column("document_metadata", "medicines")
    op.drop_column("document_metadata", "follow_up")
    op.drop_column("document_metadata", "discharge_date")
    op.drop_column("document_metadata", "admission_date")
    op.drop_column("document_metadata", "clinical_summary")
    op.drop_column("document_metadata", "diagnosis")
    op.drop_column("document_metadata", "specialization")

    op.drop_column("documents", "page_count")
