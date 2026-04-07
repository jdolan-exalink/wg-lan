"""add nat_enabled to networks

Revision ID: t3u4v5w6x7y8
Revises: s2t3u4v5w6x7
Create Date: 2026-04-07

"""
from alembic import op
import sqlalchemy as sa

revision = 't3u4v5w6x7y8'
down_revision = 's2t3u4v5w6x7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('networks', sa.Column('nat_enabled', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    op.drop_column('networks', 'nat_enabled')
