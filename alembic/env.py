"""Alembic environment script auto-generated for SQLModel metadata.

This file wires Alembic to the *runtime* SQLModel metadata defined in
`tux.database.models` so that `alembic revision --autogenerate` correctly
reflects changes to the declarative models.
"""

from __future__ import annotations

import os
from logging.config import fileConfig
from typing import Any

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# Import models so their metadata is registered.
from tux.database import models as _models  # noqa: F401  # pylint: disable=unused-import

# --------------------------------------------------------
# Alembic configuration
# --------------------------------------------------------

config = context.config  # type: ignore[attr-defined]

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)  # type: ignore[arg-type]

# Target metadata for 'autogenerate' support.
# We rely on SQLModel which stores all tables in SQLModel.metadata.

target_metadata = SQLModel.metadata  # type: ignore[attr-defined]

# Database URL: use env or alembic.ini → sqlalchemy.url

DATABASE_URL = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))

if DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    # Autogenerate uses *sync* engine - strip async driver if present.
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)


# --------------------------------------------------------
# Helper functions
# --------------------------------------------------------


def get_engine_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the SQLAlchemy Engine configuration for Alembic."""

    cfg = config.get_section(config.config_ini_section)  # type: ignore[arg-type]
    assert cfg is not None
    cfg = dict(cfg)
    cfg["sqlalchemy.url"] = DATABASE_URL
    if overrides:
        cfg.update(overrides)
    return cfg


# --------------------------------------------------------
# Offline / online migration runners
# --------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations without an Engine (generates SQL scripts)."""

    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in `online` mode with a live DB connection."""

    connectable = engine_from_config(
        get_engine_config({"sqlalchemy.echo": "False"}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# --------------------------------------------------------
# Entrypoint
# --------------------------------------------------------

if context.is_offline_mode():  # type: ignore[attr-defined]
    run_migrations_offline()
else:
    run_migrations_online()
