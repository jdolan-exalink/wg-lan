"""add ad config and group mappings

Revision ID: m6n7o8p9q0r1
Revises: k5l6m7n8o9p0
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = "m6n7o8p9q0r1"
down_revision = "k5l6m7n8o9p0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "server_config",
        sa.Column("ad_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_server", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_base_dn", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_bind_dn", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_bind_password", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_user_filter", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_group_filter", sa.String(), nullable=True),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_use_ssl", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "server_config",
        sa.Column("ad_require_membership", sa.Boolean(), nullable=False, server_default=sa.true()),
    )

    op.create_table(
        "ad_group_mappings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ad_group_dn", sa.String(), nullable=False),
        sa.Column("ad_group_name", sa.String(), nullable=False),
        sa.Column("netloom_group_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["netloom_group_id"], ["peer_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ad_group_mappings")
    op.drop_column("server_config", "ad_require_membership")
    op.drop_column("server_config", "ad_use_ssl")
    op.drop_column("server_config", "ad_group_filter")
    op.drop_column("server_config", "ad_user_filter")
    op.drop_column("server_config", "ad_bind_password")
    op.drop_column("server_config", "ad_bind_dn")
    op.drop_column("server_config", "ad_base_dn")
    op.drop_column("server_config", "ad_server")
    op.drop_column("server_config", "ad_enabled")
