"""add os to peers

Revision ID: i2j3k4l5m6n7
Revises: h1c2d3e4f5g6
Create Date: 2026-04-02

Changes:
- Add os column to peers table to store detected operating system
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'i2j3k4l5m6n7'
down_revision: Union[str, None] = '6a6cdfe0544f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('peers') as batch_op:
        batch_op.add_column(sa.Column('os', sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('peers') as batch_op:
        batch_op.drop_column('os')
