"""
Revision ID: a6716205c5f3
Revises: d66affc8b778
Create Date: 2025-09-08 03:27:19.523575+00:00
"""
from __future__ import annotations

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a6716205c5f3'
down_revision: str | None = 'd66affc8b778'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create guild_permission_levels table
    op.create_table(
        'guild_permission_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('color', sa.Integer(), nullable=True),
        sa.Column('position', sa.Integer(), nullable=False, default=0),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id', 'level', name='unique_guild_level'),
        sa.UniqueConstraint('guild_id', 'name', name='unique_guild_level_name'),
    )

    # Create indexes for guild_permission_levels
    op.create_index('idx_guild_perm_levels_guild', 'guild_permission_levels', ['guild_id'])
    op.create_index('idx_guild_perm_levels_position', 'guild_permission_levels', ['guild_id', 'position'])

    # Create guild_permission_assignments table
    op.create_table(
        'guild_permission_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('permission_level_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.BigInteger(), nullable=False),
        sa.Column('assigned_by', sa.BigInteger(), nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id', 'role_id', name='unique_guild_role_assignment'),
    )

    # Create indexes for guild_permission_assignments
    op.create_index('idx_guild_perm_assignments_guild', 'guild_permission_assignments', ['guild_id'])
    op.create_index('idx_guild_perm_assignments_level', 'guild_permission_assignments', ['permission_level_id'])
    op.create_index('idx_guild_perm_assignments_role', 'guild_permission_assignments', ['role_id'])

    # Create guild_command_permissions table
    op.create_table(
        'guild_command_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('command_name', sa.String(length=200), nullable=False),
        sa.Column('required_level', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('guild_id', 'command_name', name='unique_guild_command'),
    )

    # Create indexes for guild_command_permissions
    op.create_index('idx_guild_cmd_perms_guild', 'guild_command_permissions', ['guild_id'])
    op.create_index('idx_guild_cmd_perms_category', 'guild_command_permissions', ['guild_id', 'category'])
    op.create_index('idx_guild_cmd_perms_level', 'guild_command_permissions', ['required_level'])

    # Create guild_blacklists table
    op.create_table(
        'guild_blacklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.BigInteger(), nullable=False),
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('blacklisted_by', sa.BigInteger(), nullable=False),
        sa.Column('blacklisted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for guild_blacklists
    op.create_index('idx_guild_blacklist_guild', 'guild_blacklists', ['guild_id'])
    op.create_index('idx_guild_blacklist_target', 'guild_blacklists', ['guild_id', 'target_type', 'target_id'])
    op.create_index('idx_guild_blacklist_expires', 'guild_blacklists', ['expires_at'])

    # Create guild_whitelists table
    op.create_table(
        'guild_whitelists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.BigInteger(), nullable=False),
        sa.Column('target_type', sa.String(length=20), nullable=False),
        sa.Column('target_id', sa.BigInteger(), nullable=False),
        sa.Column('feature', sa.String(length=100), nullable=False),
        sa.Column('whitelisted_by', sa.BigInteger(), nullable=False),
        sa.Column('whitelisted_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Create indexes for guild_whitelists
    op.create_index('idx_guild_whitelist_guild', 'guild_whitelists', ['guild_id'])
    op.create_index('idx_guild_whitelist_target', 'guild_whitelists', ['guild_id', 'target_type', 'target_id'])
    op.create_index('idx_guild_whitelist_feature', 'guild_whitelists', ['guild_id', 'feature'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_guild_whitelist_feature', table_name='guild_whitelists')
    op.drop_index('idx_guild_whitelist_target', table_name='guild_whitelists')
    op.drop_index('idx_guild_whitelist_guild', table_name='guild_whitelists')

    op.drop_index('idx_guild_blacklist_expires', table_name='guild_blacklists')
    op.drop_index('idx_guild_blacklist_target', table_name='guild_blacklists')
    op.drop_index('idx_guild_blacklist_guild', table_name='guild_blacklists')

    op.drop_index('idx_guild_cmd_perms_level', table_name='guild_command_permissions')
    op.drop_index('idx_guild_cmd_perms_category', table_name='guild_command_permissions')
    op.drop_index('idx_guild_cmd_perms_guild', table_name='guild_command_permissions')

    op.drop_index('idx_guild_perm_assignments_role', table_name='guild_permission_assignments')
    op.drop_index('idx_guild_perm_assignments_level', table_name='guild_permission_assignments')
    op.drop_index('idx_guild_perm_assignments_guild', table_name='guild_permission_assignments')

    op.drop_index('idx_guild_perm_levels_position', table_name='guild_permission_levels')
    op.drop_index('idx_guild_perm_levels_guild', table_name='guild_permission_levels')

    # Drop tables
    op.drop_table('guild_whitelists')
    op.drop_table('guild_blacklists')
    op.drop_table('guild_command_permissions')
    op.drop_table('guild_permission_assignments')
    op.drop_table('guild_permission_levels')
