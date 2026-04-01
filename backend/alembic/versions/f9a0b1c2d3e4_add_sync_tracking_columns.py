"""add sync tracking columns

Revision ID: f9a0b1c2d3e4
Revises: e7f8a9b0c1d2
Create Date: 2026-04-01
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

revision = "f9a0b1c2d3e4"
down_revision = "e7f8a9b0c1d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    peers_cols = [c["name"] for c in inspector.get_columns("peers")]
    if "last_config_hash" not in peers_cols:
        op.add_column("peers", sa.Column("last_config_hash", sa.String(), nullable=True))
    if "last_config_downloaded_at" not in peers_cols:
        op.add_column("peers", sa.Column("last_config_downloaded_at", sa.DateTime(), nullable=True))

    sc_cols = [c["name"] for c in inspector.get_columns("server_config")]
    if "last_config_changed_at" not in sc_cols:
        op.add_column("server_config", sa.Column("last_config_changed_at", sa.DateTime(), nullable=True))
        op.execute("UPDATE server_config SET last_config_changed_at = datetime('now')")
        op.alter_column("server_config", "last_config_changed_at", nullable=False)


def downgrade() -> None:
    op.drop_column("server_config", "last_config_changed_at")
    op.drop_column("peers", "last_config_downloaded_at")
    op.drop_column("peers", "last_config_hash")
