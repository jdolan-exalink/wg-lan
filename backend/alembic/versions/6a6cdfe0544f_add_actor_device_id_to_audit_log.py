"""add_actor_device_id_to_audit_log

Revision ID: 6a6cdfe0544f
Revises: a3b4c5d6e7f8
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a6cdfe0544f'
down_revision: Union[str, None] = 'b4c5d6e7f8a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audit_log', sa.Column('actor_device_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'audit_log', 'devices', ['actor_device_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'audit_log', type_='foreignkey')
    op.drop_column('audit_log', 'actor_device_id')
