import asyncio
from collections.abc import Callable

import alembic_postgresql_enum  # noqa: F401
from alembic import context
from sqlalchemy import MetaData
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Import models to populate metadata
from tux.database.models import content as _content
from tux.database.models import guild as _guild
from tux.database.models import moderation as _moderation
from tux.database.models import permissions as _permissions
from tux.database.models import social as _social
from tux.database.models import starboard as _starboard
from tux.shared.config.env import get_database_url

config = context.config

if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_database_url())

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)
SQLModel.metadata.naming_convention = naming_convention  # type: ignore[attr-defined]

target_metadata = SQLModel.metadata

_keep_refs = (_content, _guild, _moderation, _permissions, _social, _starboard)


def include_object(object, name, type_, reflected, compare_to):
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
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        pool_pre_ping=True,
    )

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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
