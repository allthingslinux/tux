import os
import asyncio
from datetime import datetime, timezone

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_URL") is None,
    reason="POSTGRES_URL not set; skipping Postgres integration test",
)


@pytest.mark.asyncio
async def test_postgres_upgrade_and_basic_ops(monkeypatch):
    # Configure DEV_DATABASE_URL from POSTGRES_URL for the app
    pg_url = os.environ["POSTGRES_URL"]
    monkeypatch.setenv("DEV_DATABASE_URL", pg_url)

    # Run Alembic upgrade head
    from tux.database.migrations.runner import upgrade_head_if_needed
    # Force as non-dev to ensure upgrade triggers
    monkeypatch.setenv("TUX_ENV", "prod")
    await upgrade_head_if_needed()

    # Simple round-trip using controllers
    from tux.database.controllers import DatabaseController
    from tux.database.services.database import DatabaseService

    db_service = DatabaseService()
    controller = DatabaseController(db_service)

    guild_id = 999_000_000_000_001
    g = await controller.guild.get_or_create_guild(guild_id)
    assert g.guild_id == guild_id

    cfg = await controller.guild.update_guild_config(guild_id, {"prefix": "$"})
    assert cfg.guild_id == guild_id and cfg.prefix == "$"

    # Snippet insert and read
    created = await controller.snippet.create_snippet(
        snippet_name="IntTest",
        snippet_content="pg",
        snippet_created_at=datetime.now(timezone.utc),
        snippet_user_id=123,
        guild_id=guild_id,
    )
    fetched = await controller.snippet.get_snippet_by_name_and_guild_id("inttest", guild_id)
    assert fetched is not None and fetched.snippet_id == created.snippet_id