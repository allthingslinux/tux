"""
Revision ID: 22226ae91e2b
Revises: 87cb35799ae5
Create Date: 2025-08-31 08:59:05.502055+00:00
"""
from __future__ import annotations

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '22226ae91e2b'
down_revision: str | None = '87cb35799ae5'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
