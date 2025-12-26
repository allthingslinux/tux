"""
🚀 Database Model Performance Tests - SQLModel + py-pglite Unit Testing.

Tests for model performance characteristics.
"""

import pytest
from sqlmodel import desc, select

from tests.fixtures import TEST_GUILD_ID
from tux.database.models.models import Guild, GuildConfig
from tux.database.service import DatabaseService


class TestModelPerformance:
    """⚡ Test model performance characteristics."""

    @pytest.mark.unit
    async def test_bulk_operations(self, db_service: DatabaseService) -> None:
        """Test bulk model operations."""
        async with db_service.session() as session:
            # Create multiple guilds
            guilds = [
                Guild(id=TEST_GUILD_ID + i, case_count=i)
                for i in range(10)  # Smaller number for faster tests
            ]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Verify all were created
            statement = select(Guild)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 10

    @pytest.mark.unit
    async def test_query_performance(self, db_service: DatabaseService) -> None:
        """Test query performance with filtering and ordering."""
        async with db_service.session() as session:
            # Create test data
            guilds = [Guild(id=TEST_GUILD_ID + i, case_count=i) for i in range(20)]

            for guild in guilds:
                session.add(guild)
            await session.commit()

            # Test filtering query
            statement = select(Guild).where(Guild.case_count > 10)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 9  # case_count 11-19

            # Test ordering query
            statement = select(Guild).order_by(desc(Guild.case_count)).limit(5)
            results = (await session.execute(statement)).scalars().unique().all()
            assert len(results) == 5
            assert results[0].case_count == 19

    @pytest.mark.unit
    async def test_serialization_performance(self, db_service: DatabaseService) -> None:
        """Test serialization performance."""
        async with db_service.session() as session:
            # Create test data
            guilds = []
            configs = []

            for i in range(5):  # Create 5 test guilds with configs
                guild = Guild(id=TEST_GUILD_ID + i, case_count=i)
                session.add(guild)
                guilds.append(guild)

                config = GuildConfig(
                    id=TEST_GUILD_ID + i,
                    prefix=f"!{i}",  # Use valid prefix length (max 3 chars)
                )
                session.add(config)
                configs.append(config)

            await session.commit()

            # Serialize all models
            results = []
            for guild, config in zip(guilds, configs, strict=True):
                guild_dict = guild.to_dict()
                config_dict = config.to_dict()
                results.append({"guild": guild_dict, "config": config_dict})

            assert len(results) == 5

            # Verify serialization structure
            for result in results:
                assert "guild" in result
                assert "config" in result
                assert "id" in result["guild"]
                assert "id" in result["config"]
