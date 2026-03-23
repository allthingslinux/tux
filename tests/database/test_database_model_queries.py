"""
🚀 Database Model Query Tests - SQLModel + py-pglite Integration Testing.

Tests for complex queries and database operations using real database (py-pglite).
These are integration tests because they use a real PostgreSQL database.
"""

import pytest
from sqlalchemy import text
from sqlmodel import desc, select

from tests.fixtures import TEST_CHANNEL_ID, TEST_GUILD_ID
from tux.database.models.models import Guild, GuildConfig
from tux.database.service import DatabaseService


class TestModelQueries:
    """🔍 Test complex queries and database operations."""

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_insert_and_commit_persists_guilds_with_expected_ids(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Insert and commit guilds; persisted rows have expected ids and case_count."""
        # Arrange
        async with db_service.session() as session:
            guilds = [Guild(id=TEST_GUILD_ID + i, case_count=i) for i in range(5)]
            for guild in guilds:
                session.add(guild)
            # Act
            await session.commit()
            # Assert
            for i, guild in enumerate(guilds):
                assert guild.id == TEST_GUILD_ID + i
                assert guild.case_count == i

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_complex_queries(self, db_service: DatabaseService) -> None:
        """Filter, order, and aggregate over persisted guilds return expected results."""
        async with db_service.session() as session:
            # Arrange
            guilds = [Guild(id=TEST_GUILD_ID + i, case_count=i * 2) for i in range(10)]
            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Act & Assert - filtering
            statement = select(Guild).where(Guild.case_count > 10)
            high_case_guilds = (
                (await session.execute(statement)).scalars().unique().all()
            )
            assert len(high_case_guilds) == 4  # case_count 12, 14, 16, 18

            # Act & Assert - ordering
            statement = select(Guild).order_by(desc(Guild.case_count)).limit(3)
            top_guilds = (await session.execute(statement)).scalars().unique().all()
            assert len(top_guilds) == 3
            assert top_guilds[0].case_count == 18
            assert top_guilds[1].case_count == 16
            assert top_guilds[2].case_count == 14

            # Act & Assert - aggregation
            result = await session.execute(text("SELECT COUNT(*) FROM guild"))
            count = result.scalar()
            assert count == 10

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.asyncio
    async def test_join_queries(self, db_service: DatabaseService) -> None:
        """Join of guild and guild_config returns expected row."""
        async with db_service.session() as session:
            # Arrange
            guild = Guild(id=TEST_GUILD_ID, case_count=5)
            session.add(guild)
            await session.commit()
            config = GuildConfig(
                id=TEST_GUILD_ID,
                prefix="!j",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(config)
            await session.commit()

            # Act
            result = await session.execute(
                text("""
                SELECT g.id, g.case_count, gc.prefix
                FROM guild g
                JOIN guild_config gc ON g.id = gc.id
                WHERE g.id = :guild_id
            """),
                {"guild_id": TEST_GUILD_ID},
            )

            # Assert
            row = result.fetchone()
            assert row is not None
            assert row[0] == TEST_GUILD_ID
            assert row[1] == 5
            assert row[2] == "!j"
