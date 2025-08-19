import asyncio
from datetime import datetime, timezone

import pytest
from sqlmodel import SQLModel
from tux.database.models.guild import Guild, GuildConfig
from tux.database.models.content import Snippet

from tux.database.controllers import DatabaseController
from tux.database.services.database import DatabaseService


@pytest.mark.asyncio
async def test_smoke_guild_snippet_case_sqlite(monkeypatch, tmp_path):
    # Use a temporary SQLite file to ensure the schema persists across connections
    db_file = tmp_path / "smoke.sqlite3"
    monkeypatch.setenv("DEV_DATABASE_URL", f"sqlite+aiosqlite:///{db_file}")

    db_service = DatabaseService()
    controller = DatabaseController(db_service)

    # Create only the tables compatible with SQLite for this unit test
    async with db_service.manager.engine.begin() as conn:  # type: ignore[attr-defined]
        def _create_subset(sync_conn):
            SQLModel.metadata.create_all(
                bind=sync_conn,
                tables=[
                    Guild.__table__,
                    GuildConfig.__table__,
                    Snippet.__table__,
                ],
            )

        await conn.run_sync(_create_subset)

    guild_id = 123456789012345678

    # Guild and config
    g = await controller.guild.get_or_create_guild(guild_id)
    assert g.guild_id == guild_id

    cfg = await controller.guild.update_guild_config(guild_id, {"prefix": "!"})
    assert cfg.guild_id == guild_id and cfg.prefix == "!"

    # Snippet create and read
    created = await controller.snippet.create_snippet(
        snippet_name="Hello",
        snippet_content="world",
        snippet_created_at=datetime.now(timezone.utc),
        snippet_user_id=111,
        guild_id=guild_id,
    )
    assert created.snippet_id is not None

    fetched = await controller.snippet.get_snippet_by_name_and_guild_id("hello", guild_id)
    assert fetched is not None and fetched.snippet_id == created.snippet_id

    # Fetch guild again to ensure session/commit pipeline ok
    g2 = await controller.guild.get_guild_by_id(guild_id)
    assert g2 is not None
