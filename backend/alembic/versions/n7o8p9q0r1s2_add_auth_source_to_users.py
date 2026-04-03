"""add auth_source to users

Revision ID: n7o8p9q0r1s2
Revises: m6n7o8p9q0r1
Create Date: 2026-04-02
"""
from alembic import op
import sqlalchemy as sa

revision = "n7o8p9q0r1s2"
down_revision = "m6n7o8p9q0r1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("auth_source", sa.String(), nullable=False, server_default="local"),
    )


def downgrade() -> None:
    op.drop_column("users", "auth_source")
