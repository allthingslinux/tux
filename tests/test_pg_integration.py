"""
PostgreSQL integration test for database operations.

This test uses direct SQLModel/SQLAlchemy operations to test PostgreSQL connectivity
and basic database operations without complex controller dependencies.
"""
import os


import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select

from tux.database.models.guild import Guild, GuildConfig
from tux.database.models.content import Snippet


pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_URL") is None,
    reason="POSTGRES_URL not set; skipping Postgres integration test",
)


@pytest.mark.asyncio
async def test_postgres_basic_operations(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test basic PostgreSQL database operations."""
    # Get PostgreSQL URL from environment
    pg_url = os.environ["POSTGRES_URL"]

    # Convert to async PostgreSQL URL if needed
    if pg_url.startswith("postgresql://") and "+asyncpg" not in pg_url:
        pg_url = pg_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Create engine and session factory
    engine = create_async_engine(pg_url, echo=False)
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

        guild_id = 999_000_000_000_001

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
            config = GuildConfig(guild_id=guild_id, prefix="$")
            session.add(config)
            await session.commit()

            # Read the config back
            stmt = select(GuildConfig).where(GuildConfig.guild_id == guild_id)
            result = await session.execute(stmt)
            found_config = result.scalar_one_or_none()

            assert found_config is not None
            assert found_config.guild_id == guild_id
            assert found_config.prefix == "$"

        # Test snippet operations
        async with session_factory() as session:
            # Create a snippet
            snippet = Snippet(
                snippet_name="IntTest",
                snippet_content="pg",
                snippet_user_id=123,
                guild_id=guild_id,
            )
            session.add(snippet)
            await session.commit()

            # Read the snippet back
            stmt = select(Snippet).where(
                (Snippet.snippet_name == "inttest") & (Snippet.guild_id == guild_id),
            )
            result = await session.execute(stmt)
            found_snippet = result.scalar_one_or_none()

            assert found_snippet is not None
            assert found_snippet.snippet_name == "IntTest"
            assert found_snippet.snippet_content == "pg"
            assert found_snippet.guild_id == guild_id
            assert found_snippet.snippet_user_id == 123

        # Test data persistence across sessions
        async with session_factory() as session:
            # Verify all data is still there
            guild_count = await session.execute(select(Guild).where(Guild.guild_id == guild_id))
            assert guild_count.scalar_one_or_none() is not None

            config_count = await session.execute(select(GuildConfig).where(GuildConfig.guild_id == guild_id))
            assert config_count.scalar_one_or_none() is not None

            snippet_count = await session.execute(select(Snippet).where(Snippet.guild_id == guild_id))
            assert snippet_count.scalar_one_or_none() is not None

    finally:
        # Clean up - drop all tables
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: SQLModel.metadata.drop_all(bind=sync_conn))

        # Dispose engine
        await engine.dispose()
