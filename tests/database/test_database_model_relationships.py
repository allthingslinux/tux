"""
🚀 Database Model Relationships Tests - SQLModel + py-pglite Unit Testing.

Tests for model relationships and database constraints.
"""

import pytest
from sqlmodel import delete as sql_delete

from tests.fixtures import (
    TEST_CHANNEL_ID,
    TEST_GUILD_ID,
    validate_relationship_integrity,
)
from tux.database.models.models import Guild, GuildConfig
from tux.database.service import DatabaseService


class TestModelRelationships:
    """🔗 Test model relationships and database constraints."""

    @pytest.mark.unit
    async def test_guild_to_config_relationship(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Test relationship between Guild and GuildConfig."""
        async with db_service.session() as session:
            # Create guild
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config
            config = GuildConfig(
                id=TEST_GUILD_ID,
                prefix="!r",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )
            session.add(config)
            await session.commit()

            # Test relationship integrity
            assert validate_relationship_integrity(guild, config)

            # Test queries through relationship
            guild_from_db = await session.get(Guild, TEST_GUILD_ID)
            config_from_db = await session.get(GuildConfig, TEST_GUILD_ID)

            assert guild_from_db is not None
            assert config_from_db is not None
            assert guild_from_db.id == config_from_db.id

    @pytest.mark.unit
    async def test_foreign_key_constraints(self, db_service: DatabaseService) -> None:
        """Test foreign key constraints are enforced."""
        async with db_service.session() as session:
            # Try to create config without guild (should fail)
            config = GuildConfig(
                id=999999999999999999,  # Non-existent guild
                prefix="!f",  # Use valid prefix length (max 3 chars)
                mod_log_id=TEST_CHANNEL_ID,
            )

            session.add(config)

            # This should raise a foreign key violation
            with pytest.raises(
                Exception,
                match=r".*(foreign key|constraint).*",
            ) as exc_info:
                await session.commit()

            # Check that it's a constraint violation
            error_msg = str(exc_info.value).lower()
            assert "foreign key" in error_msg or "constraint" in error_msg
            # Rollback the session for cleanup
            await session.rollback()

    @pytest.mark.unit
    async def test_unique_constraints(self, db_service: DatabaseService) -> None:
        """Test unique constraints are enforced."""
        async with db_service.session() as session:
            # Create first guild
            guild1 = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild1)
            await session.commit()

            # Try to create duplicate guild (should fail)
            # Note: This intentionally creates an identity key conflict to test constraint behavior
            # The SAWarning is expected and indicates the test is working correctly
            guild2 = Guild(id=TEST_GUILD_ID, case_count=1)  # Same ID
            session.add(guild2)

            with pytest.raises(Exception, match=r".*(unique|constraint).*") as exc_info:
                await session.commit()

            # Check that it's a constraint violation
            error_msg = str(exc_info.value).lower()
            assert "unique" in error_msg or "constraint" in error_msg
            # Rollback the session for cleanup
            await session.rollback()

    @pytest.mark.unit
    async def test_cascade_behavior(self, db_service: DatabaseService) -> None:
        """Test cascade behavior with related models."""
        async with db_service.session() as session:
            # Create guild with config
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            config = GuildConfig(
                id=TEST_GUILD_ID,
                prefix="!c",  # Use valid prefix length (max 3 chars)
            )
            session.add(config)
            await session.commit()

            # Verify both exist
            assert await session.get(Guild, TEST_GUILD_ID) is not None
            assert await session.get(GuildConfig, TEST_GUILD_ID) is not None

            # Delete guild (config should be handled based on cascade rules)
            # Load the relationship first to ensure cascade works
            await session.refresh(guild, ["guild_config"])
            # Use delete statement to ensure cascade works at database level
            await session.execute(sql_delete(Guild).where(Guild.id == TEST_GUILD_ID))
            await session.commit()

        # Use a fresh session to verify deletion (previous session may have cached objects)
        async with db_service.session() as fresh_session:
            # Verify guild is deleted
            assert await fresh_session.get(Guild, TEST_GUILD_ID) is None

            # Verify config was also deleted (cascade behavior)
            assert await fresh_session.get(GuildConfig, TEST_GUILD_ID) is None
