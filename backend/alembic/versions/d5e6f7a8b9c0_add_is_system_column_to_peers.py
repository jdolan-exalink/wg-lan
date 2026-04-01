"""add is_system column to peers

Revision ID: d5e6f7a8b9c0
Revises: c4d6e7f8a9b0
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5e6f7a8b9c0'
down_revision = 'c4d6e7f8a9b0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('peers', sa.Column('is_system', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('peers', 'is_system')
