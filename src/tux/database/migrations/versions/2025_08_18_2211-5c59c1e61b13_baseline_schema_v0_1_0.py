"""
Revision ID: 5c59c1e61b13
Revises: df75aae067ff
Create Date: 2025-08-18 22:11:18.407320
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5c59c1e61b13'
down_revision: Union[str, None] = 'df75aae067ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
