"""add peer network access table

Revision ID: a1b2c3d4e5f6
Revises: f9a0b1c2d3e4
Create Date: 2026-04-01
"""

from alembic import op
import sqlalchemy as sa


revision = "a1b2c3d4e5f6"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "peer_network_access" in inspector.get_table_names():
        return

    op.create_table(
        "peer_network_access",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("peer_id", sa.Integer(), sa.ForeignKey("peers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("network_id", sa.Integer(), sa.ForeignKey("networks.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("peer_id", "network_id", name="uq_peer_network_access"),
    )


def downgrade() -> None:
    op.drop_table("peer_network_access")