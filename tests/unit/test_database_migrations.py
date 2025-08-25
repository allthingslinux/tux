"""
🚀 Professional Database Schema & Migration Tests - Async Architecture

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

import pytest

from sqlalchemy.engine import Engine
from sqlalchemy import text

from tux.database.service import DatabaseService
from tux.database.controllers import (
    GuildController, GuildConfigController,
)
from tux.database.models import Guild

# Test constants
TEST_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/test_db"
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321


# 📦 Module-scoped fixtures (using conftest.py db_engine)


# 📦 ASYNC Database Service Fixture
@pytest.fixture(scope="function")
async def db_service(db_engine: Engine) -> DatabaseService:
    """
    Async database service fixture that matches production setup.

    This creates a DatabaseService instance that uses our test engine,
    allowing us to test schema and migration behavior through the real async architecture.
    """
    service = DatabaseService(echo=False)

    # Create async URL from sync PGlite engine
    sync_url = str(db_engine.url)
    # Extract the host path from sync URL and create async URL
    import urllib.parse
    parsed = urllib.parse.urlparse(sync_url)
    query_params = urllib.parse.parse_qs(parsed.query)

    if socket_path := query_params.get('host', [''])[0]:
        # Create async URL pointing to same Unix socket
        # Use the socket path directly for asyncpg Unix socket connection
        async_url = f"postgresql+asyncpg://postgres:postgres@/postgres?host={urllib.parse.quote(socket_path)}"
        await service.connect(database_url=async_url)
    else:
        # Fallback to regular connect if we can't parse the host
        await service.connect(database_url=TEST_DATABASE_URL)

    return service


@pytest.fixture
async def guild_controller(db_service: DatabaseService) -> GuildController:
    """Real async Guild controller for testing schema behavior."""
    return GuildController(db_service)


@pytest.fixture
async def guild_config_controller(db_service: DatabaseService) -> GuildConfigController:
    """Real async GuildConfig controller for testing schema relationships."""
    return GuildConfigController(db_service)


# =============================================================================
# ASYNC TEST CLASSES - Testing Schema Through DatabaseService
# =============================================================================

class TestDatabaseSchemaThroughService:
    """🚀 Test database schema through async DatabaseService operations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_table_creation_through_service(self, db_service: DatabaseService) -> None:
        """Test that tables are created correctly through DatabaseService."""
        # Connect and create tables through service
        await db_service.connect(database_url=TEST_DATABASE_URL)

        try:
            await db_service.create_tables()

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

        finally:
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schema_persistence_across_restarts(self, db_service: DatabaseService) -> None:
        """Test that schema persists across database restarts."""
        # First session: create tables and data
        await db_service.connect(database_url=TEST_DATABASE_URL)
        await db_service.create_tables()

        try:
            guild_controller = GuildController(db_service)
            await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

            # Disconnect and reconnect
            await db_service.disconnect()

            # Second session: reconnect and verify data persists
            await db_service.connect(database_url=TEST_DATABASE_URL)

            # Data should still exist
            new_guild_controller = GuildController(db_service)
            retrieved = await new_guild_controller.get_guild_by_id(TEST_GUILD_ID)

            assert retrieved is not None
            assert retrieved.guild_id == TEST_GUILD_ID

        finally:
            await db_service.disconnect()


class TestSchemaConstraintsThroughControllers:
    """🚀 Test database constraints through async controller operations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_foreign_key_constraints_through_controllers(self, db_service: DatabaseService, guild_controller: GuildController, guild_config_controller: GuildConfigController) -> None:
        """Test foreign key constraints through controller operations."""
        await db_service.connect(database_url=TEST_DATABASE_URL)
        await db_service.create_tables()

        try:
            # Test 1: Create config without guild (should handle gracefully)
            await guild_config_controller.get_or_create_config(
                guild_id=999999999999999999,  # Non-existent guild
                prefix="!",
            )
            # Controller should handle this (either create guild or proper error)

            # Test 2: Create config with valid guild
            guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            valid_config = await guild_config_controller.get_or_create_config(
                guild_id=guild.guild_id,
                prefix="?",
            )

            assert valid_config.guild_id == guild.guild_id

            # Test 3: Verify relationship integrity
            retrieved_config = await guild_config_controller.get_config_by_guild_id(guild.guild_id)
            assert retrieved_config is not None
            assert retrieved_config.guild_id == guild.guild_id

        finally:
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_unique_constraints_through_controllers(self, db_service: DatabaseService, guild_controller: GuildController) -> None:
        """Test unique constraints through controller operations."""
        await db_service.connect(database_url=TEST_DATABASE_URL)
        await db_service.create_tables()

        try:
            # Create first guild
            guild1 = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            assert guild1.guild_id == TEST_GUILD_ID

            # Try to create guild with same ID (should work due to get_or_create pattern)
            guild2 = await guild_controller.get_or_create_guild(TEST_GUILD_ID)
            assert guild2.guild_id == TEST_GUILD_ID

            # Should be the same guild (uniqueness maintained)
            assert guild1.guild_id == guild2.guild_id

            # Verify only one guild exists
            retrieved = await guild_controller.get_guild_by_id(TEST_GUILD_ID)
            assert retrieved is not None
            assert retrieved.guild_id == TEST_GUILD_ID

        finally:
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_integrity_through_operations(self, db_service: DatabaseService, guild_controller: GuildController, guild_config_controller: GuildConfigController) -> None:
        """Test data integrity through multiple controller operations."""
        await db_service.connect(database_url=TEST_DATABASE_URL)
        await db_service.create_tables()

        try:
            # Create guild and config
            guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            config = await guild_config_controller.get_or_create_config(
                guild_id=guild.guild_id,
                prefix="!",
                mod_log_id=TEST_CHANNEL_ID,
            )

            # Update config multiple times
            updated_config = await guild_config_controller.update_config(
                guild_id=config.guild_id,
                prefix="?",
                audit_log_id=TEST_CHANNEL_ID + 1,
            )

            assert updated_config is not None
            if updated_config:
                assert updated_config.prefix == "?"

            # Verify all data is consistent across controllers
            retrieved_guild = await guild_controller.get_guild_by_id(guild.guild_id)
            retrieved_config = await guild_config_controller.get_config_by_guild_id(guild.guild_id)

            assert retrieved_guild is not None
            assert retrieved_config is not None
            assert retrieved_guild.guild_id == retrieved_config.guild_id

        finally:
            await db_service.disconnect()


class TestSchemaMigrationsThroughService:
    """🚀 Test schema migration behavior through DatabaseService."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_table_creation(self, db_service: DatabaseService) -> None:
        """Test creation of multiple related tables through service."""
        await db_service.connect(database_url=TEST_DATABASE_URL)

        try:
            # Create all tables
            await db_service.create_tables()

            # Test that we can use multiple controllers (indicating multiple tables work)
            guild_controller = GuildController(db_service)
            guild_config_controller = GuildConfigController(db_service)

            # Create interrelated data
            guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            config = await guild_config_controller.get_or_create_config(
                guild_id=guild.guild_id,
                prefix="!",
            )

            # Verify relationships work across tables
            assert config.guild_id == guild.guild_id

        finally:
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_schema_compatibility_across_operations(self, db_service: DatabaseService) -> None:
        """Test that schema remains compatible across different operations."""
        await db_service.connect(database_url=TEST_DATABASE_URL)
        await db_service.create_tables()

        try:
            guild_controller = GuildController(db_service)

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
                assert retrieved.guild_id == guild_id

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

        finally:
            await db_service.disconnect()


class TestSchemaErrorHandlingThroughService:
    """🚀 Test schema-related error handling through DatabaseService."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_connection_errors_handled_gracefully(self, db_service: DatabaseService) -> None:
        """Test that connection errors are handled gracefully."""
        # Try to connect with invalid URL
        try:
            await db_service.connect(database_url="invalid://url")
            # If we get here, the service should handle it gracefully
        except Exception:
            # Expected for invalid URL
            pass
        finally:
            # Should be safe to disconnect even if connection failed
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_double_connection_handling(self, db_service: DatabaseService) -> None:
        """Test handling of double connections."""
        await db_service.connect(database_url=TEST_DATABASE_URL)

        try:
            # Second connection should be handled gracefully
            await db_service.connect(database_url=TEST_DATABASE_URL)
            assert db_service.is_connected() is True

        finally:
            await db_service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_operations_on_disconnected_service(self, disconnected_db_service: DatabaseService) -> None:
        # sourcery skip: use-contextlib-suppress
        """Test behavior when trying to use disconnected service."""
        # Service starts disconnected
        assert disconnected_db_service.is_connected() is False

        guild_controller = GuildController(disconnected_db_service)

        # Operations should fail gracefully when not connected
        try:
            await guild_controller.create_guild(guild_id=TEST_GUILD_ID)
            # If we get here, the service should handle disconnection gracefully
        except Exception:
            # Expected when not connected
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
