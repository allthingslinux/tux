"""
Revision ID: 74e64998a491
Revises: b7b5361a5954
Create Date: 2025-08-19 00:44:59.732006
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '74e64998a491'
down_revision: Union[str, None] = 'b7b5361a5954'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
