"""
Revision ID: 4a949298364e
Revises: 678be63fe669
Create Date: 2025-08-19 02:03:58.292251
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a949298364e"
down_revision: str | None = "678be63fe669"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Functional index for case-insensitive lookups: lower(snippet_name), guild_id
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_snippet_lower_name_guild ON snippet (lower(snippet_name), guild_id)",
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_snippet_lower_name_guild")
