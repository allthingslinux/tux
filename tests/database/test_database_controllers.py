"""Database controllers integration tests."""

import pytest

from tux.database.controllers import (
    GuildConfigController,
    GuildController,
)

# Test constants
TEST_GUILD_ID = 123456789012345678
TEST_USER_ID = 987654321098765432
TEST_CHANNEL_ID = 876543210987654321


class TestGuildController:
    """🚀 Test Guild controller following py-pglite example patterns."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_retrieve_guild(
        self,
        guild_controller: GuildController,
    ) -> None:
        """Test guild creation and retrieval - clean and focused."""
        # Create guild using real async controller (matches actual API)
        guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        assert guild.id == TEST_GUILD_ID
        assert guild.case_count == 0  # Default value

        # Retrieve guild using real async controller
        retrieved = await guild_controller.get_guild_by_id(guild.id)
        assert retrieved is not None
        assert retrieved.id == TEST_GUILD_ID

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_or_create_guild(self, guild_controller: GuildController) -> None:
        """Test get_or_create guild functionality."""
        # First create
        guild1 = await guild_controller.get_or_create_guild(TEST_GUILD_ID)
        assert guild1.id == TEST_GUILD_ID

        # Then get existing (should return the same guild)
        guild2 = await guild_controller.get_or_create_guild(TEST_GUILD_ID)
        assert guild2.id == TEST_GUILD_ID
        # Should have the same ID
        assert guild1.id == guild2.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_guild(self, guild_controller: GuildController) -> None:
        """Test guild deletion."""
        # Create guild using real async controller
        guild = await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Delete guild using real async controller
        result = await guild_controller.delete_guild(guild.id)
        assert result is True

        # Verify deletion
        retrieved = await guild_controller.get_guild_by_id(guild.id)
        assert retrieved is None


class TestGuildConfigController:
    """🚀 Test GuildConfig controller with professional patterns."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_and_retrieve_config(
        self,
        guild_config_controller: GuildConfigController,
    ) -> None:
        """Test guild config creation and retrieval."""
        # Create guild first (foreign key requirement)
        guild_controller = GuildController(guild_config_controller.db_service)
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        # Create config using real async controller
        config = await guild_config_controller.get_or_create_config(
            guild_id=TEST_GUILD_ID,
            prefix="?",
            mod_log_id=TEST_CHANNEL_ID,
            audit_log_id=TEST_CHANNEL_ID + 1,
            starboard_channel_id=TEST_CHANNEL_ID + 2,
        )

        assert config.id == TEST_GUILD_ID
        assert config.prefix == "?"

        # Retrieve config using real async controller
        retrieved = await guild_config_controller.get_config_by_guild_id(config.id)
        assert retrieved is not None
        assert retrieved.prefix == "?"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_guild_config(
        self,
        guild_config_controller: GuildConfigController,
    ) -> None:
        """Test updating guild config."""
        # Create guild and config
        guild_controller = GuildController(guild_config_controller.db_service)
        await guild_controller.create_guild(guild_id=TEST_GUILD_ID)

        config = await guild_config_controller.get_or_create_config(
            guild_id=TEST_GUILD_ID,
            prefix="!",
        )

        # Update prefix using real async controller
        updated_config = await guild_config_controller.update_config(
            guild_id=config.id,
            prefix="?",
        )

        assert updated_config is not None
        assert updated_config.prefix == "?"

        # Verify update
        retrieved = await guild_config_controller.get_config_by_guild_id(config.id)
        assert retrieved is not None
        assert retrieved.prefix == "?"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
