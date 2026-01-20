"""
Configuration for database migration plugin.

Handles configuration for migrating from old Prisma/Supabase database
to new SQLModel/PostgreSQL database.
"""

from __future__ import annotations

import os
from typing import Any

from loguru import logger


def get_old_database_url() -> str:
    """
    Get the old database URL from environment variable.

    Returns
    -------
    str
        PostgreSQL connection URL for the old database.

    Notes
    -----
    Set OLD_DATABASE_URL for real migrations. The URL format from Supabase
    may use `postgres://` which is converted to `postgresql+psycopg://`
    for SQLAlchemy sync connections.
    """
    url = os.getenv("OLD_DATABASE_URL", "")

    # Convert postgres:// to postgresql+psycopg:// for SQLAlchemy
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
        logger.debug("Converted postgres:// to postgresql+psycopg:// for SQLAlchemy")

    return url


class MigrationConfig:
    """
    Configuration for database migration.

    Attributes
    ----------
    old_database_url : str
        Connection URL for the old Prisma/Supabase database.
    batch_size : int
        Number of records to process in each batch.
    dry_run : bool
        If True, don't commit changes (for testing).
    enabled_tables : set[str] | None
        Set of table names to migrate. If None, migrate all tables.
    """

    def __init__(
        self,
        old_database_url: str | None = None,
        batch_size: int = 1000,
        dry_run: bool = False,
        enabled_tables: set[str] | None = None,
    ) -> None:
        """
        Initialize migration configuration.

        Parameters
        ----------
        old_database_url : str | None, optional
            Old database URL. If None, uses environment variable or default.
        batch_size : int, optional
            Batch size for processing records (default: 1000).
        dry_run : bool, optional
            Enable dry-run mode (default: False).
        enabled_tables : set[str] | None, optional
            Set of table names to migrate. None means all tables.
        """
        self.old_database_url = old_database_url or get_old_database_url()
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.enabled_tables = enabled_tables

    def is_table_enabled(self, table_name: str) -> bool:
        """
        Check if a table should be migrated.

        Parameters
        ----------
        table_name : str
            Name of the table to check.

        Returns
        -------
        bool
            True if table should be migrated, False otherwise.
        """
        if self.enabled_tables is None:
            return True
        return table_name in self.enabled_tables

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns
        -------
        dict[str, Any]
            Configuration as dictionary (URLs are sanitized).
        """
        # Sanitize URL for logging (remove password)
        url_parts = self.old_database_url.split("@")
        sanitized_url = (
            url_parts[0].split(":")[0] + ":***@" + url_parts[1]
            if len(url_parts) == 2
            else "***"
        )

        return {
            "old_database_url": sanitized_url,
            "batch_size": self.batch_size,
            "dry_run": self.dry_run,
            "enabled_tables": (
                list(self.enabled_tables) if self.enabled_tables else None
            ),
        }
