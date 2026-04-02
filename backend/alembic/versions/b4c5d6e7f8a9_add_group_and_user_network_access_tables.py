"""add group and user network access tables

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-04-02

"""
from alembic import op
import sqlalchemy as sa


revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Create group_network_access table
    if "group_network_access" not in inspector.get_table_names():
        op.create_table(
            "group_network_access",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("group_id", sa.Integer(), sa.ForeignKey("peer_groups.id", ondelete="CASCADE"), nullable=False),
            sa.Column("network_id", sa.Integer(), sa.ForeignKey("networks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("action", sa.String(), nullable=False, server_default="allow"),
            sa.UniqueConstraint("group_id", "network_id", name="uq_group_network_access"),
        )
        op.create_index("ix_group_network_access_group_id", "group_network_access", ["group_id"])
        op.create_index("ix_group_network_access_network_id", "group_network_access", ["network_id"])

    # Create user_network_access table
    if "user_network_access" not in inspector.get_table_names():
        op.create_table(
            "user_network_access",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("network_id", sa.Integer(), sa.ForeignKey("networks.id", ondelete="CASCADE"), nullable=False),
            sa.Column("action", sa.String(), nullable=False, server_default="allow"),
            sa.UniqueConstraint("user_id", "network_id", name="uq_user_network_access"),
        )
        op.create_index("ix_user_network_access_user_id", "user_network_access", ["user_id"])
        op.create_index("ix_user_network_access_network_id", "user_network_access", ["network_id"])


def downgrade() -> None:
    op.drop_table("user_network_access")
    op.drop_table("group_network_access")
