"""
Revision ID: 0b1f7a2e1abc
Revises: 5c59c1e61b13
Create Date: 2025-08-18 22:30:00
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # noqa: F401
from sqlmodel import SQLModel

# Ensure models are imported so metadata is populated
import tux.database.models  # noqa: F401

# revision identifiers, used by Alembic.
revision: str = "0b1f7a2e1abc"
down_revision: Union[str, None] = "5c59c1e61b13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    SQLModel.metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    SQLModel.metadata.drop_all(bind)

