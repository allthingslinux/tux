"""
Add audit_log_message_id to cases table

Revision ID: d66affc8b778
Revises: 22226ae91e2b
Create Date: 2025-09-04 18:55:00.000000+00:00
"""
from __future__ import annotations

from typing import Union
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd66affc8b778'
down_revision: str | None = '22226ae91e2b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add audit_log_message_id column to cases table."""
    # Add the audit_log_message_id column to the cases table
    op.add_column(
        'cases',
        sa.Column(
            'audit_log_message_id',
            sa.BigInteger(),
            nullable=True,
            comment='Discord message ID for audit log message - allows editing the message if case is updated',
        ),
    )

    # Create an index on the new column for performance
    op.create_index(
        'idx_case_audit_log_message_id',
        'cases',
        ['audit_log_message_id'],
    )


def downgrade() -> None:
    """Remove audit_log_message_id column from cases table."""
    # Drop the index first
    op.drop_index('idx_case_audit_log_message_id', 'cases')

    # Drop the column
    op.drop_column('cases', 'audit_log_message_id')
