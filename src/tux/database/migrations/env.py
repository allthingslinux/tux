from __future__ import annotations

from typing import Literal

import alembic_postgresql_enum  # noqa: F401  # pyright: ignore[reportUnusedImport]
from alembic import context
from sqlalchemy import MetaData
from sqlalchemy.sql.schema import SchemaItem
from sqlmodel import SQLModel

# Import models to populate metadata
# We need to import the actual model classes, not just the modules
from tux.database.models import (
    AccessType,
    AFK,
    Case,
    CaseType,
    Guild,
    GuildConfig,
    GuildPermission,
    Levels,
    Note,
    PermissionType,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)
from tux.shared.config import CONFIG

# Get config from context if available, otherwise create a minimal one
try:
    config = context.config
except AttributeError:
    # Not in an Alembic context, create a minimal config for testing
    from alembic.config import Config
    config = Config()
    config.set_main_option("sqlalchemy.url", CONFIG.DATABASE_URL)

naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",  # More specific index naming
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",  # Support for multi-column constraints
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)
SQLModel.metadata.naming_convention = naming_convention

target_metadata = SQLModel.metadata

# Keep references to imported models to ensure they're registered
_keep_refs = (
    Snippet,
    Reminder,
    Guild,
    GuildConfig,
    Case,
    CaseType,
    Note,
    GuildPermission,
    PermissionType,
    AccessType,
    AFK,
    Levels,
    Starboard,
    StarboardMessage,
)


def include_object(
    obj: SchemaItem,
    name: str | None,
    type_: Literal["schema", "table", "column", "index", "unique_constraint", "foreign_key_constraint"],
    reflected: bool,
    compare_to: SchemaItem | None,
) -> bool:
    # Include all objects; adjust if we later want to exclude temp tables
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Use CONFIG.database_url for offline migrations too
    url = CONFIG.database_url

    # Convert to sync format for offline mode
    if url.startswith("postgresql+psycopg_async://"):
        url = url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        include_object=include_object,
        # Match online configuration for consistency
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
    """Run migrations in 'online' mode."""
    # Get the database URL from our config (auto-handles async/sync conversion)
    database_url = CONFIG.database_url

    # For Alembic operations, we need a sync URL
    # Convert async URLs to sync for Alembic compatibility
    if database_url.startswith("postgresql+psycopg_async://"):
        database_url = database_url.replace("postgresql+psycopg_async://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://"):
        # Ensure we're using psycopg3 for sync operations
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

    # Log the database URL (without password) for debugging
    import re
    debug_url = re.sub(r':([^:@]{4})[^:@]*@', r':****@', database_url)
    print(f"DEBUG: Migration database URL: {debug_url}")

    # Create a sync engine for Alembic with better connection settings
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import OperationalError
    import time

    # Retry connection a few times in case database is starting up
    max_retries = 5
    retry_delay = 2
    connectable = None

    for attempt in range(max_retries):
        try:
            connectable = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={
                    'connect_timeout': 10,
                    'options': '-c statement_timeout=300000',  # 5 minute timeout
                },
            )

            # Test the connection before proceeding
            with connectable.connect() as connection:
                connection.execute(text("SELECT 1"))
                break

        except OperationalError as e:
            if attempt == max_retries - 1:
                print(f"DEBUG: Failed to connect after {max_retries} attempts: {e}")
                raise

            print(f"DEBUG: Connection attempt {attempt + 1} failed, retrying in {retry_delay}s")

            time.sleep(retry_delay)

    if connectable is None:
        raise RuntimeError("Failed to create database connection")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,
            include_object=include_object,
            # Enhanced configuration for better migration generation
            process_revision_directives=None,
            # Additional options for better migration quality
            include_schemas=False,  # Focus on public schema
            upgrade_token="upgrades",
            downgrade_token="downgrades",
            alembic_module_prefix="op.",
            sqlalchemy_module_prefix="sa.",
            # Enable transaction per migration for safety
            transaction_per_migration=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
