"""
Revision ID: 678be63fe669
Revises: cb9d912934d3
Create Date: 2025-08-19 01:22:34.102405
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '678be63fe669'
down_revision: Union[str, None] = 'cb9d912934d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pg_trgm extension is present if we want trigram ops later (optional)
    # op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # GIN index on case.case_user_roles (jsonb array) and case.case_metadata (jsonb object)
    op.create_index(
        'ix_case_user_roles_gin', 'case', ['case_user_roles'], unique=False, postgresql_using='gin'
    )
    op.create_index(
        'ix_case_metadata_gin', 'case', ['case_metadata'], unique=False, postgresql_using='gin'
    )


def downgrade() -> None:
    op.drop_index('ix_case_metadata_gin', table_name='case')
    op.drop_index('ix_case_user_roles_gin', table_name='case')
