"""
Revision ID: cb9d912934d3
Revises: 
Create Date: 2025-08-19 00:51:42.713645
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'cb9d912934d3'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	# Minimal explicit baseline (extend with remaining tables)
	# Enum (placeholder create to ensure type exists)
	case_type_enum = sa.Enum(
		'BAN','UNBAN','HACKBAN','TEMPBAN','KICK','TIMEOUT','UNTIMEOUT','WARN','JAIL','UNJAIL','SNIPPETBAN','SNIPPETUNBAN','POLLBAN','POLLUNBAN',
		name='case_type_enum'
	)
	case_type_enum.create(op.get_bind(), checkfirst=True)

	# guild
	op.create_table(
		'guild',
		sa.Column('created_by', sa.BigInteger(), nullable=True),
		sa.Column('updated_by', sa.BigInteger(), nullable=True),
		sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
		sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('deleted_by', sa.BigInteger(), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('guild_id', sa.BigInteger(), primary_key=True),
		sa.Column('guild_joined_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('case_count', sa.Integer(), server_default='0', nullable=False),
	)
	op.create_index('idx_guild_id', 'guild', ['guild_id'])

	# guild_config
	op.create_table(
		'guild_config',
		sa.Column('created_by', sa.BigInteger(), nullable=True),
		sa.Column('updated_by', sa.BigInteger(), nullable=True),
		sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
		sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('deleted_by', sa.BigInteger(), nullable=True),
		sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
		sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
		sa.Column('guild_id', sa.BigInteger(), sa.ForeignKey('guild.guild_id'), primary_key=True),
		sa.Column('prefix', sa.String(length=10), nullable=True),
		sa.Column('mod_log_id', sa.BigInteger(), nullable=True),
		sa.Column('audit_log_id', sa.BigInteger(), nullable=True),
		sa.Column('join_log_id', sa.BigInteger(), nullable=True),
		sa.Column('private_log_id', sa.BigInteger(), nullable=True),
		sa.Column('report_log_id', sa.BigInteger(), nullable=True),
		sa.Column('dev_log_id', sa.BigInteger(), nullable=True),
		sa.Column('jail_channel_id', sa.BigInteger(), nullable=True),
		sa.Column('general_channel_id', sa.BigInteger(), nullable=True),
		sa.Column('starboard_channel_id', sa.BigInteger(), nullable=True),
		sa.Column('base_staff_role_id', sa.BigInteger(), nullable=True),
		sa.Column('base_member_role_id', sa.BigInteger(), nullable=True),
		sa.Column('jail_role_id', sa.BigInteger(), nullable=True),
		sa.Column('quarantine_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_0_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_1_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_2_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_3_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_4_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_5_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_6_role_id', sa.BigInteger(), nullable=True),
		sa.Column('perm_level_7_role_id', sa.BigInteger(), nullable=True),
	)


def downgrade() -> None:
	op.drop_table('guild_config')
	op.drop_index('idx_guild_id', table_name='guild')
	op.drop_table('guild')
	sa.Enum(name='case_type_enum').drop(op.get_bind(), checkfirst=True)