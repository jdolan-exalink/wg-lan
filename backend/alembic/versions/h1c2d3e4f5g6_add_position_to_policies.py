"""add position to policies

Revision ID: h1c2d3e4f5g6
Revises: f9a0b1c2d3e4
Create Date: 2026-04-02

Changes:
- Add position column to policies table for user-defined rule ordering
- Initialize position = id so existing rules keep their natural order
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'h1c2d3e4f5g6'
down_revision: Union[str, None] = 'a2b3c4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('policies') as batch_op:
        batch_op.add_column(sa.Column('position', sa.Integer(), nullable=False, server_default='0'))

    # Set initial position = id so existing policies keep their natural insertion order
    op.execute("UPDATE policies SET position = id")


def downgrade() -> None:
    with op.batch_alter_table('policies') as batch_op:
        batch_op.drop_column('position')
