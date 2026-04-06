"""add ip groups and dest_ip_group_id to policies

Revision ID: s2t3u4v5w6x7
Revises: n7o8p9q0r1s2
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa

revision = "s2t3u4v5w6x7"
down_revision = "n7o8p9q0r1s2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ip_groups",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("network_id", sa.Integer(), sa.ForeignKey("networks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("name", name="uq_ip_group_name"),
    )

    op.create_table(
        "ip_group_entries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ip_group_id", sa.Integer(), sa.ForeignKey("ip_groups.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ip_address", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("ip_group_id", "ip_address", name="uq_ip_group_entry"),
    )

    op.add_column("policies", sa.Column("dest_ip_group_id", sa.Integer(), sa.ForeignKey("ip_groups.id", ondelete="CASCADE"), nullable=True))

    dest_group_col = op.get_bind().dialect.name
    op.drop_constraint("uq_policy_source_dest_direction", "policies", type_="unique")
    op.create_unique_constraint("uq_policy_source_dest_direction", "policies", ["source_group_id", "dest_group_id", "dest_ip_group_id", "direction"])


def downgrade() -> None:
    op.drop_constraint("uq_policy_source_dest_direction", "policies", type_="unique")
    op.create_unique_constraint("uq_policy_source_dest_direction", "policies", ["source_group_id", "dest_group_id", "direction"])

    op.drop_column("policies", "dest_ip_group_id")
    op.drop_table("ip_group_entries")
    op.drop_table("ip_groups")
