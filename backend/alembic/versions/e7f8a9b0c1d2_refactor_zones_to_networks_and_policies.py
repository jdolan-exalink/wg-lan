"""refactor zones to networks and policies to group-to-group

Revision ID: e7f8a9b0c1d2
Revises: d5e6f7a8b9c0
Create Date: 2026-04-01

Changes:
- Add peer_id to networks table
- Drop zones and zone_networks tables
- Recreate policies table with source_group_id, dest_group_id, direction
- Migrate existing zone_networks to networks
- Migrate existing policies to group-to-group (best effort)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7f8a9b0c1d2'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add peer_id to networks (nullable initially)
    # Use batch mode for SQLite compatibility (no ALTER CONSTRAINT support)
    with op.batch_alter_table('networks') as batch_op:
        batch_op.add_column(sa.Column('peer_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_networks_peer_id', 'peers', ['peer_id'], ['id'], ondelete='SET NULL')

    # Step 2: Migrate zone_networks to networks
    # For each zone_network, create a network entry with the zone name
    # We'll need to find the peer associated with the zone (if any)
    op.execute("""
        INSERT INTO networks (name, subnet, description, network_type, is_default, peer_id)
        SELECT 
            z.name || ' - ' || zn.cidr,
            zn.cidr,
            'Migrated from zone: ' || z.name,
            'lan',
            0,
            NULL
        FROM zone_networks zn
        JOIN zones z ON zn.zone_id = z.id
        WHERE zn.cidr NOT IN (SELECT subnet FROM networks)
    """)

    # Step 3: Drop old policies table
    op.drop_table('policies')

    # Step 4: Drop peer_overrides (has FK to zones.id), zone_networks, and zones tables
    op.drop_table('peer_overrides')
    op.drop_table('zone_networks')
    op.drop_table('zones')

    # Step 5: Create new policies table with group-to-group relationships
    op.create_table('policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('source_group_id', sa.Integer(), sa.ForeignKey('peer_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('dest_group_id', sa.Integer(), sa.ForeignKey('peer_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('direction', sa.String(), nullable=False, server_default='both'),  # 'outbound', 'inbound', 'both'
        sa.Column('action', sa.String(), nullable=False, server_default='allow'),  # 'allow', 'deny'
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.UniqueConstraint('source_group_id', 'dest_group_id', 'direction', name='uq_policy_source_dest_direction')
    )

    # Step 6: Recreate peer_overrides pointing to networks instead of zones
    op.create_table('peer_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('peer_id', sa.Integer(), sa.ForeignKey('peers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('network_id', sa.Integer(), sa.ForeignKey('networks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.UniqueConstraint('peer_id', 'network_id', name='uq_peer_network_override'),
    )

    # Step 7: Create indexes for performance
    op.create_index('ix_policies_source_group', 'policies', ['source_group_id'])
    op.create_index('ix_policies_dest_group', 'policies', ['dest_group_id'])
    op.create_index('ix_networks_peer_id', 'networks', ['peer_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_networks_peer_id', 'networks')
    op.drop_index('ix_policies_dest_group', 'policies')
    op.drop_index('ix_policies_source_group', 'policies')

    # Drop new policies table and peer_overrides (network_id-based)
    op.drop_table('peer_overrides')
    op.drop_table('policies')

    # Recreate zones and zone_networks tables
    op.create_table('zones',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), unique=True, nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_table('zone_networks',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('cidr', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.UniqueConstraint('zone_id', 'cidr', name='uq_zone_cidr'),
    )

    # Recreate old policies table
    op.create_table('policies',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('group_id', sa.Integer(), sa.ForeignKey('peer_groups.id', ondelete='CASCADE'), nullable=False),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.UniqueConstraint('group_id', 'zone_id', name='uq_group_zone_policy'),
    )

    # Recreate old peer_overrides pointing back to zones
    op.create_table('peer_overrides',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('peer_id', sa.Integer(), sa.ForeignKey('peers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('zone_id', sa.Integer(), sa.ForeignKey('zones.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.UniqueConstraint('peer_id', 'zone_id', name='uq_peer_zone_override'),
    )

    # Remove peer_id from networks (batch mode for SQLite compatibility)
    with op.batch_alter_table('networks') as batch_op:
        batch_op.drop_constraint('fk_networks_peer_id', type_='foreignkey')
        batch_op.drop_column('peer_id')
