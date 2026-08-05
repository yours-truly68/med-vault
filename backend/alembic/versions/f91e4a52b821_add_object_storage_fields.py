"""add_object_storage_fields

Revision ID: f91e4a52b821
Revises: 30c68f890645
Create Date: 2026-08-06 00:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f91e4a52b821'
down_revision: Union[str, None] = '30c68f890645'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('bucket', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('checksum', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('documents', 'checksum')
    op.drop_column('documents', 'bucket')
