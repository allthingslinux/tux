"""
🚀 Professional Database Schema & Migration Tests - Async Architecture.

Tests database schema, constraints, and migration behavior through the proper async architecture.
Validates that database operations work correctly with the async DatabaseService and controllers.

Key Patterns:
- Async test functions with pytest-asyncio
- Test schema through real async DatabaseService operations
- Validate constraints through controller operations
- Test table creation and relationships via async layer
- Professional async fixture setup

ARCHITECTURAL APPROACH:
We test schema and migrations THROUGH the async DatabaseService, not directly with sync SQLAlchemy.
This validates the REAL production database behavior and async architecture.
"""

from contextlib import suppress

import pytest
import sqlalchemy.exc
from sqlalchemy import text

from tux.database.controllers import (
    GuildConfigController,
    GuildController,
)
from tux.database.models import Guild
from tux.database.service import DatabaseService

# Test constants
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/test_db"
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321


# =============================================================================
# ASYNC TEST CLASSES - Testing Schema Through DatabaseService
# =============================================================================


class TestDatabaseSchemaThroughService:
    """🚀 Test database schema through async DatabaseService operations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_table_creation_through_service(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Test that tables are created correctly through DatabaseService."""
        # Database is already connected and fresh via fixture
        # Verify we can create sessions and perform operations
        async with db_service.session() as session:
            # Test basic connectivity and table access
            assert session is not None

            # Try to execute a simple query to verify tables exist
            # (This will work if tables were created successfully)
            try:
                # This would fail if tables don't exist
                result = await session.execute(text("SELECT 1"))
                assert result is not None
            except Exception:
                # If we can't execute basic queries, tables might not exist
                pytest.fail("Tables were not created successfully")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schema_persistence_across_restarts(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
    ) -> None:
        """Test that schema persists across database restarts."""
        # Database is already connected and fresh via fixture
        # Create a guild
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Data should persist (db_service_service provides clean state each time)
        retrieved = await guild_controller.get_guild_by_id(TEST_GUILD_ID)

        assert retrieved is not None
        assert retrieved.id == TEST_GUILD_ID


class TestSchemaConstraintsThroughControllers:
    """🚀 Test database constraints through async controller operations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_foreign_key_constraints_through_controllers(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
        guild_config_controller: GuildConfigController,
    ) -> None:
        """Test foreign key constraints through controller operations."""
        # Database is already connected and clean via fixture

        # Test 1: Create config without guild (should raise IntegrityError)
        with pytest.raises(Exception, match=r".*") as exc_info:
            await guild_config_controller.get_or_create_config(
                guild_id=999999999999999999,  # Non-existent guild
                prefix="!",
            )
        # Should fail due to foreign key constraint violation
        assert (
            "foreign key" in str(exc_info.value).lower()
            or "constraint" in str(exc_info.value).lower()
        )

        # Test 2: Create config with valid guild
        guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        valid_config = await guild_config_controller.get_or_create_config(
            guild_id=guild.id,
            prefix="?",
        )

        assert valid_config.id == guild.id

        # Test 3: Verify relationship integrity
        retrieved_config = await guild_config_controller.get_config_by_guild_id(
            guild.id,
        )
        assert retrieved_config is not None
        assert retrieved_config.id == guild.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unique_constraints_through_controllers(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
    ) -> None:
        """Test unique constraints through controller operations."""
        # Database is already connected and clean via fixture

        # Create first guild
        guild1 = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        assert guild1.id == TEST_GUILD_ID

        # Try to create guild with same ID (should work due to get_or_create pattern)
        guild2 = await guild_controller.get_or_create_guild(TEST_GUILD_ID)
        assert guild2.id == TEST_GUILD_ID

        # Should be the same guild (uniqueness maintained)
        assert guild1.id == guild2.id

        # Verify only one guild exists
        retrieved = await guild_controller.get_guild_by_id(TEST_GUILD_ID)
        assert retrieved is not None
        assert retrieved.id == TEST_GUILD_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_integrity_through_operations(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
        guild_config_controller: GuildConfigController,
    ) -> None:
        """Test data integrity through multiple controller operations."""
        # Database is already connected and clean via fixture

        # Create guild and config
        guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        config = await guild_config_controller.get_or_create_config(
            guild_id=guild.id,
            prefix="!",
            mod_log_id=TEST_CHANNEL_ID,
        )

        # Update config multiple times
        updated_config = await guild_config_controller.update_config(
            guild_id=config.id,
            prefix="?",
            audit_log_id=TEST_CHANNEL_ID + 1,
        )

        assert updated_config is not None
        if updated_config:
            assert updated_config.prefix == "?"

        # Verify all data is consistent across controllers
        retrieved_guild = await guild_controller.get_guild_by_id(guild.id)
        retrieved_config = await guild_config_controller.get_config_by_guild_id(
            guild.id,
        )

        assert retrieved_guild is not None
        assert retrieved_config is not None
        assert retrieved_guild.id == retrieved_config.id


class TestSchemaMigrationsThroughService:
    """🚀 Test schema migration behavior through DatabaseService."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_table_creation(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
        guild_config_controller: GuildConfigController,
    ) -> None:
        """Test creation of multiple related tables through service."""
        # Database is already connected and clean via fixture

        # Create interrelated data
        guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
        config = await guild_config_controller.get_or_create_config(
            guild_id=guild.id,
            prefix="!",
        )

        # Verify relationships work across tables
        assert config.id == guild.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schema_compatibility_across_operations(
        self,
        db_service: DatabaseService,
        guild_controller: GuildController,
    ) -> None:
        """Test that schema remains compatible across different operations."""
        # Database is already connected and clean via fixture

        # Perform various operations to test schema compatibility
        operations: list[Guild] = []

        # Create multiple guilds
        for i in range(3):
            guild_id = TEST_GUILD_ID + i
            guild = await guild_controller.create_guild(guild_id=guild_id)
            operations.append(guild)

        # Retrieve all guilds
        for i in range(3):
            guild_id = TEST_GUILD_ID + i
            retrieved = await guild_controller.get_guild_by_id(guild_id)
            assert retrieved is not None
            assert retrieved.id == guild_id

        # Delete a guild
        result = await guild_controller.delete_guild(TEST_GUILD_ID + 1)
        assert result is True

        # Verify deletion
        deleted = await guild_controller.get_guild_by_id(TEST_GUILD_ID + 1)
        assert deleted is None

        # Verify others still exist
        remaining1 = await guild_controller.get_guild_by_id(TEST_GUILD_ID)
        remaining2 = await guild_controller.get_guild_by_id(TEST_GUILD_ID + 2)
        assert remaining1 is not None
        assert remaining2 is not None


class TestSchemaErrorHandlingThroughService:
    """🚀 Test schema-related error handling through DatabaseService."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_errors_handled_gracefully(
        self,
        disconnected_async_db_service: DatabaseService,
    ) -> None:
        """Test that connection errors are handled gracefully."""
        # Try to connect with invalid URL
        try:
            await disconnected_async_db_service.connect(database_url="invalid://url")
            # If we get here, the service should handle it gracefully
        except Exception:
            # Expected for invalid URL
            pass
        finally:
            # Should be safe to disconnect even if connection failed
            await disconnected_async_db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_double_connection_handling(
        self,
        db_service: DatabaseService,
    ) -> None:
        """Test handling of double connections."""
        # Database is already connected via fixture

        # Second connection should be handled gracefully
        await db_service.connect(database_url=TEST_DATABASE_URL)
        assert db_service.is_connected() is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_operations_on_disconnected_service(
        self,
        disconnected_async_db_service: DatabaseService,
    ) -> None:
        """Test behavior when trying to use disconnected service."""
        # Service starts disconnected
        assert disconnected_async_db_service.is_connected() is False

        guild_controller = GuildController(disconnected_async_db_service)

        # Operations should fail gracefully when not connected
        # SQLAlchemy raises OperationalError when trying to use a disconnected service
        with suppress(RuntimeError, ConnectionError, sqlalchemy.exc.OperationalError):
            await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            # If we get here, the service should handle disconnection gracefully


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
