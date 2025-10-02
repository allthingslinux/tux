"""
Revision ID: ce4511224739
Revises:
Create Date: 2025-10-02 04:39:35.216539+00:00
"""
from __future__ import annotations

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'ce4511224739'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
