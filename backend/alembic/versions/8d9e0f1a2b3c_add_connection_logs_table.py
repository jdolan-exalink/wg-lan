"""Add connection_logs table

Revision ID: 8d9e0f1a2b3c
Revises: b3c5991dc6b6
Create Date: 2026-03-31 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d9e0f1a2b3c'
down_revision: Union[str, None] = 'b3c5991dc6b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('connection_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('timestamp', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('peer_id', sa.Integer(), nullable=True),
    sa.Column('peer_name', sa.String(), nullable=True),
    sa.Column('peer_ip', sa.String(), nullable=True),
    sa.Column('event_type', sa.String(), nullable=False),
    sa.Column('severity', sa.String(), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('details', sa.Text(), nullable=True),
    sa.Column('source_ip', sa.String(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['peer_id'], ['peers.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('connection_logs')
