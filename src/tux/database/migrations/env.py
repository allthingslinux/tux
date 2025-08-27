from collections.abc import Callable
from typing import Any, Literal, cast

import alembic_postgresql_enum  # noqa: F401  # pyright: ignore[reportUnusedImport]
from alembic import context
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
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
from tux.shared.config.env import get_database_url

# Get config from context if available, otherwise create a minimal one
try:
    config = context.config
except AttributeError:
    # Not in an Alembic context, create a minimal config for testing
    from alembic.config import Config
    config = Config()
    config.set_main_option("sqlalchemy.url", get_database_url())

naming_convention = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",  # More specific index naming
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",  # Support for multi-column constraints
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)
SQLModel.metadata.naming_convention = naming_convention  # type: ignore[attr-defined]

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
    url = config.get_main_option("sqlalchemy.url")
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
    """Run migrations in 'online' mode - handles both sync and async."""
    # Check if pytest-alembic has provided a connection
    connectable = context.config.attributes.get("connection", None)

    if connectable is None:
        # Get configuration section, providing default URL if not found
        config_section = config.get_section(config.config_ini_section, {})

        # If URL is not in the config section, get it from our environment function
        if "sqlalchemy.url" not in config_section:
            from tux.shared.config.env import get_database_url
            config_section["sqlalchemy.url"] = get_database_url()

        connectable = async_engine_from_config(
            config_section,
            prefix="sqlalchemy.",
            pool_pre_ping=True,
        )

    # Handle both sync and async connections
    if hasattr(connectable, 'connect') and hasattr(connectable, 'dispose') and hasattr(connectable, '_is_asyncio'):
        # This is an async engine - run async migrations
        import asyncio
        asyncio.run(run_async_migrations(connectable))
    elif hasattr(connectable, 'connect'):
        # It's a sync engine, get connection from it
        with cast(Connection, connectable.connect()) as connection:
            do_run_migrations(connection)
    else:
        # It's already a connection
        do_run_migrations(connectable)  # type: ignore[arg-type]


async def run_async_migrations(connectable: Any) -> None:
    """Run async migrations when we have an async engine."""
    async with connectable.connect() as connection:
        callback: Callable[[Connection], None] = do_run_migrations
        await connection.run_sync(callback)

    await connectable.dispose()


def do_run_migrations(connection: Connection) -> None:
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


# Only run migrations if we're in an Alembic context

# sourcery skip: use-contextlib-suppress
import contextlib
with contextlib.suppress(NameError):
    try:
        if hasattr(context, 'is_offline_mode') and context.is_offline_mode():
            run_migrations_offline()
    except (AttributeError, NameError):
        # Context is not available or not properly initialized
        pass
