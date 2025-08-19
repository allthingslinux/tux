from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from tux.shared.config.env import get_database_url, is_dev_mode


def _find_project_root(start: Path) -> Path:
    path = start.resolve()
    for parent in [path] + list(path.parents):
        if (parent / "alembic.ini").exists():
            return parent
    # Fallback to current working directory
    return Path.cwd()


def _build_alembic_config() -> Config:
    root = _find_project_root(Path(__file__))
    cfg = Config(str(root / "alembic.ini"))
    # Allow env.py to fill if missing, but set explicitly for clarity
    cfg.set_main_option("sqlalchemy.url", get_database_url())
    return cfg


async def upgrade_head_if_needed() -> None:
    """Run Alembic upgrade to head in non-dev environments.

    This call is idempotent and safe to run on startup. In dev, we skip to
    allow local workflows to manage migrations explicitly.
    """
    if is_dev_mode():
        return

    cfg = _build_alembic_config()
    # Alembic commands are synchronous; run in a thread to avoid blocking.
    await asyncio.to_thread(command.upgrade, cfg, "head")

