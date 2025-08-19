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
    pass


def downgrade() -> None:
    pass
