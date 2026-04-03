"""add ports and vpn_domain to server_config

Revision ID: k5l6m7n8o9p0
Revises: l5m6n7o8p9q0
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = "k5l6m7n8o9p0"
down_revision = "l5m6n7o8p9q0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "server_config",
        sa.Column("admin_port", sa.Integer(), nullable=False, server_default="7777"),
    )
    op.add_column(
        "server_config",
        sa.Column("api_http_port", sa.Integer(), nullable=False, server_default="7771"),
    )
    op.add_column(
        "server_config",
        sa.Column("api_https_port", sa.Integer(), nullable=False, server_default="7772"),
    )
    op.add_column(
        "server_config",
        sa.Column("api_http_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "server_config",
        sa.Column("vpn_domain", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("server_config", "vpn_domain")
    op.drop_column("server_config", "api_http_enabled")
    op.drop_column("server_config", "api_https_port")
    op.drop_column("server_config", "api_http_port")
    op.drop_column("server_config", "admin_port")