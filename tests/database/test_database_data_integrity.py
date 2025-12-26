"""
🚀 Database Data Integrity Tests - SQLModel + py-pglite Unit Testing.

Tests for data integrity and validation rules.
"""

import pytest

from tests.fixtures import TEST_GUILD_ID
from tux.database.models.models import Guild, GuildConfig
from tux.database.service import DatabaseService


class TestDataIntegrity:
    """🛡️ Test data integrity and validation rules."""

    @pytest.mark.unit
    async def test_required_fields(self, db_service: DatabaseService) -> None:
        """Test required field validation."""
        async with db_service.session() as session:
            # Guild requires id, test that it works when provided
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Verify guild was created successfully
            assert guild.id == TEST_GUILD_ID

    @pytest.mark.unit
    async def test_data_types(self, db_service: DatabaseService) -> None:
        """Test data type enforcement."""
        async with db_service.session() as session:
            # Test integer fields
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Verify types are preserved
            assert isinstance(guild.id, int)
            assert isinstance(guild.case_count, int)

    @pytest.mark.unit
    async def test_null_handling(self, db_service: DatabaseService) -> None:
        """Test NULL value handling for optional fields."""
        async with db_service.session() as session:
            # Create guild with minimal data
            guild = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild)
            await session.commit()

            # Create config with minimal data (most fields optional)
            config = GuildConfig(id=TEST_GUILD_ID)
            session.add(config)
            await session.commit()
            await session.refresh(config)

            # Verify NULL handling
            assert config.id == TEST_GUILD_ID
            assert config.prefix == "$"  # Default value, not None
            assert config.mod_log_id is None  # Optional field

    @pytest.mark.unit
    async def test_transaction_rollback(self, db_service: DatabaseService) -> None:
        """Test transaction rollback behavior."""
        async with db_service.session() as session:
            # First commit a valid guild
            guild1 = Guild(id=TEST_GUILD_ID, case_count=0)
            session.add(guild1)
            await session.commit()  # Commit first guild

            # Verify guild was committed
            result = await session.get(Guild, TEST_GUILD_ID)
            assert result is not None
            assert result.case_count == 0

            # Now try to add duplicate in a new transaction
            # Note: This intentionally creates an identity key conflict to test constraint behavior
            # The SAWarning is expected and indicates the test is working correctly
            try:
                guild2 = Guild(id=TEST_GUILD_ID, case_count=1)  # Same ID - should fail
                session.add(guild2)
                await session.commit()  # This should fail due to unique constraint
            except Exception:  # IntegrityError or similar constraint violation
                await session.rollback()  # Rollback the failed transaction

            # Verify original guild still exists and wasn't affected by the rollback
            result = await session.get(Guild, TEST_GUILD_ID)
            assert result is not None
            assert result.case_count == 0  # Original value preserved
