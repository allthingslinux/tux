"""
Revision ID: b6b36fdfad3b
Revises:
Create Date: 2025-10-09 09:40:49.515049+00:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b6b36fdfad3b'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop unused columns from guild_permission_ranks table
    op.drop_column('guild_permission_ranks', 'color')
    op.drop_column('guild_permission_ranks', 'position')
    op.drop_column('guild_permission_ranks', 'enabled')

    # Drop enabled column from guild_command_permissions table
    op.drop_column('guild_command_permissions', 'enabled')


def downgrade() -> None:
    # Add back the dropped columns to guild_permission_ranks table
    op.add_column('guild_permission_ranks',
                  sa.Column('color', sa.BigInteger(), nullable=True))
    op.add_column('guild_permission_ranks',
                  sa.Column('position', sa.Integer(), nullable=False, default=0))
    op.add_column('guild_permission_ranks',
                  sa.Column('enabled', sa.Boolean(), nullable=False, default=True))

    # Add back enabled column to guild_command_permissions table
    op.add_column('guild_command_permissions',
                  sa.Column('enabled', sa.Boolean(), nullable=False, default=True))
