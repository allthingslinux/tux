"""
Revision ID: df75aae067ff
Revises: a970ae164b81
Create Date: 2025-08-18 21:08:57.326208
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'df75aae067ff'
down_revision: Union[str, None] = 'a970ae164b81'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
