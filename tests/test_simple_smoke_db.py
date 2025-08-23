"""
Simple smoke test for database operations.

This test uses direct SQLModel/SQLAlchemy operations to avoid complex controller dependencies.
"""
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select

from tux.database.models.guild import Guild, GuildConfig
from tux.database.models.content import Snippet


@pytest.mark.asyncio
async def test_simple_database_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Simple smoke test for basic database operations."""
    # Use a temporary SQLite file
    db_file: Path = tmp_path / "test.sqlite3"
    database_url = f"sqlite+aiosqlite:///{db_file}"

    # Create engine and session factory
    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(
                lambda sync_conn: SQLModel.metadata.create_all(
                    bind=sync_conn,
                    tables=[
                        Guild.__table__,  # type: ignore[attr-defined]
                        GuildConfig.__table__,  # type: ignore[attr-defined]
                        Snippet.__table__,  # type: ignore[attr-defined]
                    ],
                ),
            )

        guild_id = 123456789012345678

        # Test basic guild operations
        async with session_factory() as session:
            # Create a guild
            guild = Guild(guild_id=guild_id)
            session.add(guild)
            await session.commit()

            # Read the guild back
            stmt = select(Guild).where(Guild.guild_id == guild_id)
            result = await session.execute(stmt)
            found_guild = result.scalar_one_or_none()

            assert found_guild is not None
            assert found_guild.guild_id == guild_id

        # Test guild config operations
        async with session_factory() as session:
            # Create guild config
            config = GuildConfig(guild_id=guild_id, prefix="!")
            session.add(config)
            await session.commit()

            # Read the config back
            stmt = select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            result = await session.execute(stmt)
            found_config = result.scalar_one_or_none()

            assert found_config is not None
            assert found_config.guild_id == guild_id
            assert found_config.prefix == "!"

        # Test snippet operations
        async with session_factory() as session:
            # Create a snippet
            snippet = Snippet(
                snippet_name="test",
                snippet_content="Hello World",
                snippet_user_id=111,
                guild_id=guild_id,
            )
            session.add(snippet)
            await session.commit()

            # Read the snippet back
            stmt = select(Snippet).where(
                (Snippet.snippet_name == "test") & (Snippet.guild_id == guild_id),
            )
            result = await session.execute(stmt)
            found_snippet = result.scalar_one_or_none()

            assert found_snippet is not None
            assert found_snippet.snippet_name == "test"
            assert found_snippet.snippet_content == "Hello World"
            assert found_snippet.guild_id == guild_id
            assert found_snippet.snippet_user_id == 111

    finally:
        # Clean up
        await engine.dispose()
