"""
Alembic Migration Environment Configuration.

This module configures Alembic's migration environment for the Tux Discord bot.
It provides both offline (SQL generation) and online (database execution) migration
modes with production-ready features including:

- Automatic retry logic with exponential backoff for Docker/CI environments
- Connection pre-testing before running migrations
- Async-to-sync URL conversion for Alembic compatibility
- Empty migration prevention for cleaner revision history
- Object filtering for views and external tables
- Comprehensive safety features and timeout configuration

Key Features
------------
- Database URL conversion: postgresql+psycopg_async:// → postgresql+psycopg://
- Retry logic: 5 attempts with 2-second backoff for database startup delays
- Connection testing: Validates connectivity with SELECT 1 before migrations
- Smart filtering: Prevents empty migrations and handles views correctly
- Type safety: Properly typed hooks for include_object and process_revision_directives
- Production config: Pool management, timeouts, and transaction safety

Configuration Options
--------------------
All options are set for maximum safety and compatibility:
- compare_type: Detect column type changes
- compare_server_default: Detect server default changes
- render_as_batch: Better ALTER TABLE support
- transaction_per_migration: Individual transaction rollback safety
- include_schemas: Disabled to prevent schema confusion
"""

from __future__ import annotations  # noqa: I001

import re
import time
from collections.abc import Iterable
from typing import Literal

from alembic import context
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from loguru import logger
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.schema import SchemaItem

from tux.database.models import (
    AFK,
    Case,
    CaseType,
    Guild,
    GuildConfig,
    Levels,
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
    PermissionType,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)
from tux.shared.config import CONFIG

from sqlmodel import SQLModel


# =============================================================================
# ALEMBIC CONFIGURATION
# =============================================================================

# Get config from context if available, otherwise create a minimal one for testing
try:
    config = context.config
except AttributeError:
    from alembic.config import Config

    config = Config()
    config.set_main_option("sqlalchemy.url", CONFIG.DATABASE_URL)

# =============================================================================
# NAMING CONVENTIONS
# =============================================================================
# Standardized constraint naming for better migration tracking and debugging

naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)
SQLModel.metadata.naming_convention = naming_convention
target_metadata = SQLModel.metadata

# =============================================================================
# MODEL REGISTRATION
# =============================================================================
# Keep references to ensure all models are registered with SQLModel metadata
# This prevents models from being garbage collected before migration detection

_keep_refs = (
    AFK,
    Case,
    CaseType,
    Guild,
    GuildConfig,
    Levels,
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
    PermissionType,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)


# =============================================================================
# MIGRATION HOOKS AND CALLBACKS
# =============================================================================


def include_object(
    obj: SchemaItem,
    name: str | None,
    type_: Literal[
        "schema",
        "table",
        "column",
        "index",
        "unique_constraint",
        "foreign_key_constraint",
    ],
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    """
    Filter schema objects for autogenerate operations.

    This hook allows fine-grained control over which database objects are
    included in migration detection and generation.

    Parameters
    ----------
    obj : SchemaItem
        The SQLAlchemy schema object being considered.
    name : str | None
        The name of the object.
    type_ : str
        The type of object (table, index, column, etc.).
    reflected : bool
        Whether the object was reflected from the database.
    compare_to : SchemaItem | None
        The corresponding object in the metadata (None if not present).

    Returns
    -------
    bool
        True to include the object, False to exclude it.

    Examples
    --------
    - Exclude views marked with info={'is_view': True}
    - Could exclude alembic_version table if needed
    - Could exclude temporary or external tables
    """
    # Exclude views from autogenerate (mark with __table_args__ = {'info': {'is_view': True}})
    return not (
        type_ == "table" and hasattr(obj, "info") and obj.info.get("is_view", False)
    )


def process_revision_directives(
    ctx: MigrationContext,
    revision: str | Iterable[str | None] | Iterable[str],
    directives: list[MigrationScript],
) -> None:
    """
    Process and potentially modify migration directives before generation.

    This hook prevents generation of empty migration files when using
    autogenerate, keeping the revision history clean and meaningful.

    Parameters
    ----------
    ctx : MigrationContext
        The current migration context.
    revision : str | Iterable
        The revision identifier(s).
    directives : list[MigrationScript]
        The migration directives to process.

    Notes
    -----
    When autogenerate detects no schema changes, this hook empties the
    directives list, preventing creation of an empty migration file.
    """
    if getattr(config.cmd_opts, "autogenerate", False):
        script = directives[0]
        if script.upgrade_ops is not None and script.upgrade_ops.is_empty():
            directives[:] = []
            logger.info(
                "No schema changes detected, skipping migration file generation",
            )


# =============================================================================
# MIGRATION EXECUTION MODES
# =============================================================================


def run_migrations_offline() -> None:
    """
    Run migrations in offline (SQL script generation) mode.

    In this mode, Alembic generates SQL scripts without connecting to a
    database. Useful for generating migration SQL to review or execute manually.

    The context is configured with just a database URL, and all operations
    are rendered as SQL statements that are emitted to the script output.

    Notes
    -----
    - Converts async database URLs to sync format for compatibility
    - Generates literal SQL with bound parameters
    - No actual database connection is made
    """
    # Convert async database URL to sync format for offline mode
    url = CONFIG.database_url
    if url.startswith("postgresql+psycopg_async://"):
        url = url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        include_schemas=False,
        upgrade_token="upgrades",
        downgrade_token="downgrades",
        alembic_module_prefix="op.",
        sqlalchemy_module_prefix="sa.",
        transaction_per_migration=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in online (database connection) mode.

    This is the standard mode for executing migrations against a live database.
    It connects to the database, runs migrations within transactions, and
    includes production-ready features like retry logic and connection testing.

    Features
    --------
    - **URL Conversion**: Automatically converts async URLs to sync for Alembic
    - **Retry Logic**: 5 attempts with 2-second delays for Docker/CI startup
    - **Connection Testing**: Validates database connectivity before migrations
    - **Pool Management**: Configured for production with pre-ping and recycling
    - **Timeout Protection**: 5-minute statement timeout prevents hung migrations
    - **Transaction Safety**: Each migration runs in its own transaction

    Configuration Details
    --------------------
    - pool_pre_ping: Tests connections before use (handles stale connections)
    - pool_recycle: Recycles connections after 1 hour (prevents timeout issues)
    - connect_timeout: 10-second connection timeout
    - statement_timeout: 5-minute query timeout (300,000ms)
    - transaction_per_migration: Individual rollback capability per migration

    Raises
    ------
    OperationalError
        If database connection fails after all retry attempts.
    RuntimeError
        If engine creation succeeds but connection is None (should never happen).

    Notes
    -----
    The retry logic is critical for Docker and CI environments where the
    database container may still be starting up when migrations are attempted.
    """
    # Convert async database URL to sync format (Alembic doesn't support async)
    database_url = CONFIG.database_url
    if database_url.startswith("postgresql+psycopg_async://"):
        database_url = database_url.replace(
            "postgresql+psycopg_async://",
            "postgresql+psycopg://",
            1,
        )

    # Log sanitized database URL (mask password for security)
    debug_url = re.sub(r":([^:@]{4})[^:@]*@", r":****@", database_url)
    logger.debug(f"Migration database URL: {debug_url}")

    # Retry configuration for Docker/CI environments
    max_retries = 5
    retry_delay = 2  # seconds
    connectable = None

    for attempt in range(max_retries):
        try:
            connectable = create_engine(
                database_url,
                pool_pre_ping=True,  # Test connections before use
                pool_recycle=3600,  # Recycle connections after 1 hour
                connect_args={
                    "connect_timeout": 10,  # 10-second connection timeout
                    "options": "-c statement_timeout=300000",  # 5-minute query timeout
                },
            )

            # Validate connection before proceeding with migrations
            with connectable.connect() as connection:
                connection.execute(text("SELECT 1"))
                break

        except OperationalError as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed to connect after {max_retries} attempts: {e}")
                raise

            logger.warning(
                f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s",
            )
            time.sleep(retry_delay)

    if connectable is None:
        msg = "Failed to create database connection"
        raise RuntimeError(msg)

    # Execute migrations with comprehensive safety configuration
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Schema change detection
            compare_type=True,  # Detect column type changes
            compare_server_default=True,  # Detect server default changes
            # Migration rendering
            render_as_batch=True,  # Better ALTER TABLE support
            # Custom hooks
            process_revision_directives=process_revision_directives,  # Prevent empty migrations
            include_object=include_object,  # Filter unwanted objects
            # Schema handling
            include_schemas=False,  # Single schema operation
            # Token customization
            upgrade_token="upgrades",
            downgrade_token="downgrades",
            alembic_module_prefix="op.",
            sqlalchemy_module_prefix="sa.",
            # Transaction management
            transaction_per_migration=True,  # Individual rollback per migration
        )

        with context.begin_transaction():
            context.run_migrations()


# =============================================================================
# MIGRATION EXECUTION
# =============================================================================
# Automatically detect mode and run appropriate migration strategy

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
