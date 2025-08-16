"""
Revision ID: a970ae164b81
Revises: 1d5137ad51e9
Create Date: 2025-08-16 21:44:20.766346
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a970ae164b81'
down_revision: Union[str, None] = '1d5137ad51e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
