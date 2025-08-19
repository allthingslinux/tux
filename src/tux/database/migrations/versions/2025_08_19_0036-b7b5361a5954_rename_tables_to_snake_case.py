"""
Revision ID: b7b5361a5954
Revises: 0b1f7a2e1abc
Create Date: 2025-08-19 00:36:48.521832
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7b5361a5954'
down_revision: Union[str, None] = '0b1f7a2e1abc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables to snake_case to align with BaseModel __tablename__ policy
    op.rename_table('guildconfig', 'guild_config')
    op.rename_table('starboardmessage', 'starboard_message')
    op.rename_table('customcasetype', 'custom_case_type')
    op.rename_table('guildpermission', 'guild_permission')


def downgrade() -> None:
    # Revert table names to previous style
    op.rename_table('guild_config', 'guildconfig')
    op.rename_table('starboard_message', 'starboardmessage')
    op.rename_table('custom_case_type', 'customcasetype')
    op.rename_table('guild_permission', 'guildpermission')
