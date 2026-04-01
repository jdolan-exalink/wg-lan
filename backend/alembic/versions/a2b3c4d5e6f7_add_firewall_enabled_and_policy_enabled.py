"""add firewall_enabled to server_config and enabled to policies

Revision ID: a2b3c4d5e6f7
Revises: f9a0b1c2d3e4
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add firewall_enabled to server_config (default False = permissive/all-allow)
    op.add_column(
        "server_config",
        sa.Column("firewall_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Add enabled to policies (default True = rule is active)
    op.add_column(
        "policies",
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("policies", "enabled")
    op.drop_column("server_config", "firewall_enabled")
