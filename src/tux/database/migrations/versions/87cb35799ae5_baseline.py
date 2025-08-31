"""
Revision ID: 87cb35799ae5
Revises:
Create Date: 2025-08-28 17:45:58.796405+00:00
"""
from __future__ import annotations

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '87cb35799ae5'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
