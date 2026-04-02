"""add managed peers and user management tables

Revision ID: a3b4c5d6e7f8
Revises: h1c2d3e4f5g6
Create Date: 2026-04-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3b4c5d6e7f8'
down_revision: Union[str, None] = 'h1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector, table: str, column: str) -> bool:
    return column in [c['name'] for c in inspector.get_columns(table)]


def _table_exists(inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ── Extend users table ──────────────────────────────────────
    if not _column_exists(inspector, 'users', 'email'):
        op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    if not _column_exists(inspector, 'users', 'is_active'):
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    if not _column_exists(inspector, 'users', 'last_failed_login_at'):
        op.add_column('users', sa.Column('last_failed_login_at', sa.DateTime(), nullable=True))
    if not _column_exists(inspector, 'users', 'failed_login_count'):
        op.add_column('users', sa.Column('failed_login_count', sa.Integer(), nullable=False, server_default='0'))

    # ── Extend peer_groups table ────────────────────────────────
    if not _column_exists(inspector, 'peer_groups', 'is_active'):
        op.add_column('peer_groups', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))

    # ── Extend peers table ──────────────────────────────────────
    if not _column_exists(inspector, 'peers', 'user_id'):
        op.add_column('peers', sa.Column('user_id', sa.Integer(), nullable=True))
    if not _column_exists(inspector, 'peers', 'device_id'):
        op.add_column('peers', sa.Column('device_id', sa.Integer(), nullable=True))
    if not _column_exists(inspector, 'peers', 'config_revision'):
        op.add_column('peers', sa.Column('config_revision', sa.Integer(), nullable=False, server_default='0'))

    # ── Create refresh_tokens table ─────────────────────────────
    if not _table_exists(inspector, 'refresh_tokens'):
        op.create_table(
            'refresh_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('token_hash', sa.String(), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('revoked_at', sa.DateTime(), nullable=True),
            sa.Column('user_agent', sa.String(), nullable=True),
            sa.Column('ip_address', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_refresh_tokens_token_hash', 'refresh_tokens', ['token_hash'])

    # ── Create devices table ────────────────────────────────────
    if not _table_exists(inspector, 'devices'):
        op.create_table(
            'devices',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('device_name', sa.String(), nullable=False),
            sa.Column('hostname', sa.String(), nullable=True),
            sa.Column('os_type', sa.String(), nullable=True),
            sa.Column('device_fingerprint', sa.String(), nullable=True),
            sa.Column('status', sa.String(), nullable=False, server_default='active'),
            sa.Column('last_seen_at', sa.DateTime(), nullable=True),
            sa.Column('last_sync_at', sa.DateTime(), nullable=True),
            sa.Column('config_revision', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_devices_device_fingerprint', 'devices', ['device_fingerprint'])

    # ── Create config_revisions table ───────────────────────────
    if not _table_exists(inspector, 'config_revisions'):
        op.create_table(
            'config_revisions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('peer_id', sa.Integer(), nullable=True),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('revision_number', sa.Integer(), nullable=False),
            sa.Column('change_type', sa.String(), nullable=False),
            sa.Column('changes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['peer_id'], ['peers.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id'),
        )
        op.create_index('ix_config_revisions_revision_number', 'config_revisions', ['revision_number'])

    # ── Create user_groups table ────────────────────────────────
    if not _table_exists(inspector, 'user_groups'):
        op.create_table(
            'user_groups',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('group_id', sa.Integer(), nullable=False),
            sa.Column('assigned_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['group_id'], ['peer_groups.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', 'group_id', name='uq_user_group'),
            sa.PrimaryKeyConstraint('id'),
        )

    # ── Add foreign keys (SQLite may need them added separately) ──
    # Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT for FKs
    # The FKs are defined in the ORM models and will work at the application level


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _table_exists(inspector, 'user_groups'):
        op.drop_table('user_groups')
    if _table_exists(inspector, 'config_revisions'):
        op.drop_index('ix_config_revisions_revision_number', table_name='config_revisions')
        op.drop_table('config_revisions')
    if _table_exists(inspector, 'devices'):
        op.drop_index('ix_devices_device_fingerprint', table_name='devices')
        op.drop_table('devices')
    if _table_exists(inspector, 'refresh_tokens'):
        op.drop_index('ix_refresh_tokens_token_hash', table_name='refresh_tokens')
        op.drop_table('refresh_tokens')

    # Remove columns from peers
    if _column_exists(inspector, 'peers', 'config_revision'):
        op.drop_column('peers', 'config_revision')
    if _column_exists(inspector, 'peers', 'device_id'):
        op.drop_column('peers', 'device_id')
    if _column_exists(inspector, 'peers', 'user_id'):
        op.drop_column('peers', 'user_id')

    # Remove column from peer_groups
    if _column_exists(inspector, 'peer_groups', 'is_active'):
        op.drop_column('peer_groups', 'is_active')

    # Remove columns from users
    if _column_exists(inspector, 'users', 'failed_login_count'):
        op.drop_column('users', 'failed_login_count')
    if _column_exists(inspector, 'users', 'last_failed_login_at'):
        op.drop_column('users', 'last_failed_login_at')
    if _column_exists(inspector, 'users', 'is_active'):
        op.drop_column('users', 'is_active')
    if _column_exists(inspector, 'users', 'email'):
        op.drop_column('users', 'email')
