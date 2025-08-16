import asyncio
from collections.abc import Callable
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# Import models to populate metadata
from tux.database.models import content as _content  # noqa: F401
from tux.database.models import guild as _guild  # noqa: F401
from tux.database.models import moderation as _moderation  # noqa: F401
from tux.database.models import permissions as _permissions  # noqa: F401
from tux.database.models import social as _social  # noqa: F401
from tux.database.models import starboard as _starboard  # noqa: F401
from tux.shared.config.env import get_database_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Skip fileConfig to avoid requiring logging sections

# Ensure sqlalchemy.url is set, fallback to app environment
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_database_url())

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = SQLModel.metadata

# Keep imported model modules referenced to avoid static analyzers from
# pruning side-effect imports that register models with SQLModel metadata.
_keep_refs = (_content, _guild, _moderation, _permissions, _social, _starboard)


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
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
