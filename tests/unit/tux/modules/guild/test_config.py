"""Unit tests for the Config cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.modules.guild.config import Config
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def config_cog(mock_bot_with_container):
    """Create a Config cog instance with mocked dependencies."""
    return Config(mock_bot_with_container)


@pytest.mark.asyncio
class TestConfigCog:
    """Test cases for the Config cog."""

    async def test_cog_initialization(self, config_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert config_cog.bot is not None
        assert config_cog.db_service is not None
        assert hasattr(config_cog, 'db')  # Backward compatibility
        assert hasattr(config_cog, 'db_config')

    async def test_config_set_logs_public(self, config_cog):
        """Test setting public logs configuration."""
        # Mock interaction
        interaction = Mock()
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        with patch('tux.ui.views.config.ConfigSetPublicLogs') as mock_view_class:
            mock_view = Mock()
            mock_view_class.return_value = mock_view

            await config_cog.config_set_logs(interaction, "Public")

            # Verify defer was called
            interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Verify correct view was created
            mock_view_class.assert_called_once()

            # Verify followup was sent
            interaction.followup.send.assert_called_once_with(view=mock_view, ephemeral=True)

    async def test_config_set_logs_private(self, config_cog):
        """Test setting private logs configuration."""
        # Mock interaction
        interaction = Mock()
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        with patch('tux.ui.views.config.ConfigSetPrivateLogs') as mock_view_class:
            mock_view = Mock()
            mock_view_class.return_value = mock_view

            await config_cog.config_set_logs(interaction, "Private")

            # Verify defer was called
            interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Verify correct view was created
            mock_view_class.assert_called_once()

            # Verify followup was sent
            interaction.followup.send.assert_called_once_with(view=mock_view, ephemeral=True)

    async def test_config_set_channels(self, config_cog):
        """Test setting channels configuration."""
        # Mock interaction
        interaction = Mock()
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        with patch('tux.ui.views.config.ConfigSetChannels') as mock_view_class:
            mock_view = Mock()
            mock_view_class.return_value = mock_view

            await config_cog.config_set_channels(interaction)

            # Verify defer was called
            interaction.response.defer.assert_called_oith(ephemeral=True)

            # Verify view was created
            mock_view_class.assert_called_once()

            # Verify followup was sent
            interaction.followup.send.assert_called_once_with(view=mock_view, ephemeral=True)

    async def test_config_set_perms(self, config_cog):
        """Test setting permission level role."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock setting choice
        setting = Mock()
        setting.value = "3"

        # Mock role
        role = Mock()
        role.id = 67890
        role.mention = "<@&67890>"

        # Mock database
        config_cog.db_config.update_perm_level_role = AsyncMock()

        await config_cog.config_set_perms(interaction, setting, role)

        # Verify defer was called
        interaction.response.defer.assert_called_once_with(ephemeral=True)

        # Verify database update
        config_cog.db_config.update_perm_level_role.assert_called_once_with(12345, "3", 67890)

        # Verify response
        interaction.followup.send.assert_called_once_with(
            "Perm level 3 role set to <@&67890>.", ephemeral=True,
        )

    async def test_config_set_roles_jail(self, config_cog):
        """Test setting jail role."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock setting choice
        setting = Mock()
        setting.value = "jail_role_id"

        # Mock role
        role = Mock()
        role.id = 67890
        role.mention = "<@&67890>"

        # Mock database
        config_cog.db_config.update_jail_role_id = AsyncMock()

        await config_cog.config_set_roles(interaction, setting, role)

        # Verify defer was called
        interaction.response.defer.assert_called_once_with(ephemeral=True)

        # Verify database update
        config_cog.db_config.update_jail_role_id.assert_called_once_with(12345, 67890)

        # Verify response
        interaction.followup.send.assert_called_once_with(
            "jail_role_id role set to <@&67890>.", ephemeral=True,
        )

    async def test_config_get_roles(self, config_cog):
        """Test getting roles configuration."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock database response
        config_cog.db_config.get_jail_role_id = AsyncMock(return_value=67890)

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_embed.add_field = Mock()
            mock_create_embed.return_value = mock_embed

            await config_cog.config_get_roles(interaction)

            # Verify defer was called
            interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Verify database query
            config_cog.db_config.get_jail_role_id.assert_called_once_with(12345)

            # Verify embed creation
            mock_create_embed.assert_called_once()
            mock_embed.add_field.assert_called_once_with(name="Jail Role", value="<@&67890>", inline=False)

            # Verify response
            interaction.followup.send.assert_called_once_with(embed=mock_embed, ephemeral=True)

    async def test_config_get_perms(self, config_cog):
        """Test getting permission levels configuration."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock database responses
        config_cog.db_config.get_perm_level_role = AsyncMock(
            side_effect=[
                11111, 22222, None, 44444, None, None, None, 88888,
            ],
        )

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_embed.add_field = Mock()
            mock_create_embed.return_value = mock_embed

            await config_cog.config_get_perms(interaction)

            # Verify defer was called
            interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Verify database queries for all 8 permission levels
            assert config_cog.db_config.get_perm_level_role.call_count == 8

            # Verify embed fields were added
            assert mock_embed.add_field.call_count == 8

            # Verify response
            interaction.followup.send.assert_called_once_with(embed=mock_embed, ephemeral=True)

    async def test_config_set_prefix(self, config_cog):
        """Test setting guild prefix."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.user = Mock()
        interaction.user.name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "http://example.com/avatar.png"
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock database
        config_cog.db_config.update_guild_prefix = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await config_cog.config_set_prefix(interaction, "!")

            # Verify defer was called
            interaction.response.defer.assert_called_once_with(ephemeral=True)

            # Verify database update
            config_cog.db_config.update_guild_prefix.assert_called_once_with(12345, "!")

            # Verify embed creation
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert "prefix was updated to `!`" in call_args['description']

            # Verify response
            interaction.followup.send.assert_called_once_with(embed=mock_embed)

    async def test_config_clear_prefix(self, config_cog):
        """Test clearing guild prefix."""
        # Mock interaction
        interaction = Mock()
        interaction.guild = Mock()
        interaction.guild.id = 12345
        interaction.user = Mock()
        interaction.user.name = "TestUser"
        interaction.user.display_avatar = Mock()
        interaction.user.display_avatar.url = "http://example.com/avatar.png"
        interaction.response = Mock()
        interaction.response.defer = AsyncMock()
        interaction.followup = Mock()
        interaction.followup.send = AsyncMock()

        # Mock database
        config_cog.db_config.delete_guild_prefix = AsyncMock()

        with patch('tux.modules.guild.config.CONFIG') as mock_config:
            mock_config.DEFAULT_PREFIX = "$"

            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await config_cog.config_clear_prefix(interaction)

                # Verify defer was called
                interaction.response.defer.assert_called_once_with(ephemeral=True)

                # Verify database update
                config_cog.db_config.delete_guild_prefix.assert_called_once_with(12345)

                # Verify embed creation
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert "prefix was reset to `$`" in call_args['description']

                # Verify response
                interaction.followup.send.assert_called_once_with(embed=mock_embed)

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        cog = Config(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, config_cog):
        """Test the string representation of the cog."""
        repr_str = repr(config_cog)
        assert "Config" in repr_str
        assert "injection=" in repr_str
