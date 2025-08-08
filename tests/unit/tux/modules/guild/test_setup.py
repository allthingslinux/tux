"""Unit tests for the Setup cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.modules.guild.setup import Setup
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def setup_cog(mock_bot_with_container):
    """Create a Setup cog instance with mocked dependencies."""
    return Setup(mock_bot_with_container)


@pytest.mark.asyncio
class TestSetupCog:
    """Test cases for the Setup cog."""

    async def test_cog_initialization(self, setup_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert setup_cog.bot is not None
        assert setup_cog.db_service is not None
        assert hasattr(setup_cog, 'db')  # Backward compatibility
        assert hasattr(setup_cog, 'config')

    async def test_setup_jail_no_jail_role(self, setup_cog):
        """Test setup jail when no jail role is configured."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        # Mock config to return no jail role
        setup_cog.config.get_guild_config_field_value = AsyncMock(return_value=None)

        await setup_cog.setup_jail(interaction)

        # Verify config was checked
        setup_cog.config.get_guild_config_field_value.assert_called_once_with(12345, "jail_role_id")

        # Verify error response
        interaction.response.send_message.assert_called_once_with(
            "No jail role has been set up for this server.", ephemeral=True,
        )

    async def test_setup_jail_role_deleted(self, setup_cog):
        """Test setup jail when jail role has been deleted."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.guild.get_role = Mock(return_value=None)  # Role deleted
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        # Mock config to return jail role ID
        setup_cog.config.get_guild_config_field_value = AsyncMock(return_value=67890)

        await setup_cog.setup_jail(interaction)

        # Verify role lookup
        interaction.guild.get_role.assert_called_once_with(67890)

        # Verify error response
        interaction.response.send_message.assert_called_once_with(
            "The jail role has been deleted.", ephemeral=True,
        )

    async def test_setup_jail_no_jail_channel(self, setup_cog):
        """Test setup jail when no jail channel is configured."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.send_message = AsyncMock()

        # Mock jail role
        mock_jail_role = Mock()
        interaction.guild.get_role = Mock(return_value=mock_jail_role)

        # Mock config responses
        setup_cog.config.get_guild_config_field_value = AsyncMock(side_effect=[67890, None])

        await setup_cog.setup_jail(interaction)

        # Verify config calls
        assert setup_cog.config.get_guild_config_field_value.call_count == 2
        setup_cog.config.get_guild_config_field_value.assert_any_call(12345, "jail_role_id")
        setup_cog.config.get_guild_config_field_value.assert_any_call(12345, "jail_channel_id")

        # Verify error response
        interaction.response.send_message.assert_called_once_with(
            "No jail channel has been set up for this server.", ephemeral=True,
        )

    async def test_setup_jail_success(self, setup_cog):
        """Test successful jail setup."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.edit_original_response = AsyncMock()

        # Mock jail role
        mock_jail_role = Mock()
        interaction.guild.get_role = Mock(return_value=mock_jail_role)

        # Mock config responses
        setup_cog.config.get_guild_config_field_value = AsyncMock(side_effect=[67890, 11111])

        # Mock permission setting
        setup_cog._set_permissions_for_channels = AsyncMock()

        await setup_cog.setup_jail(interaction)

        # Verify defer was called
        interaction.response.defer.assert_called_once_with(ephemeral=True)

        # Verify permissions were set
        setup_cog._set_permissions_for_channels.assert_called_once_with(interaction, mock_jail_role, 11111)

        # Verify success response
        interaction.edit_original_response.assert_called_once_with(
            content="Permissions have been set up for the jail role.",
        )

    async def test_set_permissions_for_channels(self, setup_cog):
        """Test setting permissions for channels."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.edit_original_response = AsyncMock()

        # Mock jail role
        mock_jail_role = Mock()
        jail_channel_id = 11111

        # Mock channels
        mock_text_channel = Mock()
        mock_text_channel.id = 22222
        mock_text_channel.name = "general"
        mock_text_channel.set_permissions = AsyncMock()
        mock_text_channel.overwrites = {}

        mock_jail_channel = Mock()
        mock_jail_channel.id = jail_channel_id
        mock_jail_channel.name = "jail"
        mock_jail_channel.set_permissions = AsyncMock()
        mock_jail_channel.overwrites = {}

        mock_voice_channel = Mock()
        mock_voice_channel.id = 33333
        mock_voice_channel.name = "voice"
        mock_voice_channel.set_permissions = AsyncMock()
        mock_voice_channel.overwrites = {}

        # Mock channel types
        import discord
        mock_text_channel.__class__ = discord.TextChannel
        mock_jail_channel.__class__ = discord.TextChannel
        mock_voice_channel.__class__ = discord.VoiceChannel

        interaction.guild.channels = [mock_text_channel, mock_jail_channel, mock_voice_channel]

        await setup_cog._set_permissions_for_channels(interaction, mock_jail_role, jail_channel_id)

        # Verify permissions were set for all channels
        mock_text_channel.set_permissions.assert_called_once_with(
            mock_jail_role, send_messages=False, read_messages=False,
        )
        mock_voice_channel.set_permissions.assert_called_once_with(
            mock_jail_role, send_messages=False, read_messages=False,
        )

        # Verify jail channel got special permissions
        assert mock_jail_channel.set_permissions.call_count == 2
        mock_jail_channel.set_permissions.assert_any_call(
            mock_jail_role, send_messages=False, read_messages=False,
        )
        mock_jail_channel.set_permissions.assert_any_call(
            mock_jail_role, send_messages=True, read_messages=True,
        )

        # Verify progress updates
        assert interaction.edit_original_response.call_count >= 3

    async def test_set_permissions_skip_existing_overwrites(self, setup_cog):
        """Test that existing correct overwrites are skipped."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.edit_original_response = AsyncMock()

        # Mock jail role
        mock_jail_role = Mock()
        jail_channel_id = 11111

        # Mock channel with existing correct overwrites
        mock_channel = Mock()
        mock_channel.id = 22222
        mock_channel.name = "general"
        mock_channel.set_permissions = AsyncMock()

        # Mock existing overwrites
        mock_overwrite = Mock()
        mock_overwrite.send_messages = False
        mock_overwrite.read_messages = False
        mock_channel.overwrites = {mock_jail_role: mock_overwrite}

        import discord
        mock_channel.__class__ = discord.TextChannel

        interaction.guild.channels = [mock_channel]

        await setup_cog._set_permissions_for_channels(interaction, mock_jail_role, jail_channel_id)

        # Verify permissions were not set (skipped)
        mock_channel.set_permissions.assert_not_called()

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        cog = Setup(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, setup_cog):
        """Test the string representation of the cog."""
        repr_str = repr(setup_cog)
        assert "Setup" in repr_str
        assert "injection=" in repr_str
