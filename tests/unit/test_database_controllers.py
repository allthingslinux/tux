import pytest
from collections.abc import Generator

from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine

from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

from tux.database.controllers import (
    GuildController, GuildConfigController,
)


# Test constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321


@pytest.fixture(scope="module")
def sqlalchemy_pglite_engine() -> Generator[Engine]:
    """Module-scoped PGlite engine for clean test isolation."""
    manager = SQLAlchemyPGliteManager(PGliteConfig())
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager.get_engine()
    finally:
        manager.stop()


@pytest.fixture(scope="function")
def sqlalchemy_session(sqlalchemy_pglite_engine: Engine) -> Generator[Session]:
    """Function-scoped session with automatic cleanup."""
    session_local = sessionmaker(bind=sqlalchemy_pglite_engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


class TestGuildController:
    """🚀 Test Guild controller following py-pglite example patterns."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_retrieve_guild(self, integration_guild_controller: GuildController) -> None:
        """Test guild creation and retrieval - clean and focused."""
        # Create guild using real async controller (matches actual API)
        guild = await integration_guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        assert guild.guild_id == TEST_GUILD_ID
        assert guild.case_count == 0  # Default value

        # Retrieve guild using real async controller
        retrieved = await integration_guild_controller.get_guild_by_id(guild.guild_id)
        assert retrieved is not None
        assert retrieved.guild_id == TEST_GUILD_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_or_create_guild(self, integration_guild_controller: GuildController) -> None:
        """Test get_or_create guild functionality."""
        # First create
        guild1 = await integration_guild_controller.get_or_create_guild(TEST_GUILD_ID)
        assert guild1.guild_id == TEST_GUILD_ID

        # Then get existing (should return the same guild)
        guild2 = await integration_guild_controller.get_or_create_guild(TEST_GUILD_ID)
        assert guild2.guild_id == TEST_GUILD_ID
        # Should have the same ID
        assert guild1.guild_id == guild2.guild_id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_guild(self, integration_guild_controller: GuildController) -> None:
        """Test guild deletion."""
        # Create guild using real async controller
        guild = await integration_guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Delete guild using real async controller
        result = await integration_guild_controller.delete_guild(guild.guild_id)
        assert result is True

        # Verify deletion
        retrieved = await integration_guild_controller.get_guild_by_id(guild.guild_id)
        assert retrieved is None


class TestGuildConfigController:
    """🚀 Test GuildConfig controller with professional patterns."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_retrieve_config(self, integration_guild_config_controller: GuildConfigController) -> None:
        """Test guild config creation and retrieval."""
        # Create guild first (foreign key requirement)
        guild_controller = GuildController(integration_guild_config_controller.db_service)
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Create config using real async controller
        config = await integration_guild_config_controller.get_or_create_config(
            guild_id=TEST_GUILD_ID,
            prefix="?",
            mod_log_id=TEST_CHANNEL_ID,
            audit_log_id=TEST_CHANNEL_ID + 1,
            starboard_channel_id=TEST_CHANNEL_ID + 2,
        )

        assert config.guild_id == TEST_GUILD_ID
        assert config.prefix == "?"

        # Retrieve config using real async controller
        retrieved = await integration_guild_config_controller.get_config_by_guild_id(config.guild_id)
        assert retrieved is not None
        assert retrieved.prefix == "?"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_guild_config(self, integration_guild_config_controller: GuildConfigController) -> None:
        """Test updating guild config."""
        # Create guild and config
        guild_controller = GuildController(integration_guild_config_controller.db_service)
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        config = await integration_guild_config_controller.get_or_create_config(
            guild_id=TEST_GUILD_ID,
            prefix="!",
        )

        # Update prefix using real async controller
        updated_config = await integration_guild_config_controller.update_config(
            guild_id=config.guild_id,
            prefix="?",
        )

        assert updated_config is not None
        assert updated_config.prefix == "?"

        # Verify update
        retrieved = await integration_guild_config_controller.get_config_by_guild_id(config.guild_id)
        assert retrieved is not None
        assert retrieved.prefix == "?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
