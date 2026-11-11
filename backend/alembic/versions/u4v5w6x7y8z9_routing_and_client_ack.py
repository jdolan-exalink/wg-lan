"""Explicit LAN next hops and client application acknowledgements."""
from alembic import op
import sqlalchemy as sa

revision = "u4v5w6x7y8z9"
down_revision = "t3u4v5w6x7y8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("networks", sa.Column("gateway_ip", sa.String(), nullable=True))
    op.add_column("peers", sa.Column("desired_config_hash", sa.String(), nullable=True))
    op.add_column("peers", sa.Column("applied_config_revision", sa.Integer(), nullable=True))
    op.add_column("peers", sa.Column("last_config_applied_at", sa.DateTime(), nullable=True))
    op.add_column("peers", sa.Column("last_seen_at", sa.DateTime(), nullable=True))


def downgrade():
    for column in ("last_seen_at", "last_config_applied_at", "applied_config_revision", "desired_config_hash"):
        op.drop_column("peers", column)
    op.drop_column("networks", "gateway_ip")
