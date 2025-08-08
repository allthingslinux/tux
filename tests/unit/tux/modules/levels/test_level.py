"""Unit tests for the Level cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.modules.levels.level import Level
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def level_cog(mock_bot_with_container):
    """Create a Level cog instance with mocked dependencies."""
    with patch('tux.modules.levels.level.generate_usage'):
        with patch('tux.modules.levels.level.LevelsService') as mock_levels_service:
            mock_service_instance = Mock()
            mock_levels_service.return_value = mock_service_instance
            cog = Level(mock_bot_with_container)
            cog.levels_service = mock_service_instance
            return cog


@pytest.mark.asyncio
class TestLevelCog:
    """Test cases for the Level cog."""

    async def test_cog_initialization(self, level_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert level_cog.bot is not None
        assert level_cog.db_service is not None
        assert hasattr(level_cog, 'db')  # Backward compatibility
        assert hasattr(level_cog, 'levels_service')

    async def test_level_command_no_guild(self, level_cog):
        """Test level command when not in a guild."""
        # Mock context without guild
        ctx = Mock()
        ctx.guild = None
        ctx.send = AsyncMock()

        await level_cog.level(ctx)

        ctx.send.assert_called_once_with("This command can only be executed within a guild.")

    async def test_level_command_self(self, level_cog):
        """Test level command for the command author."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.send = AsyncMock()

        # Mock database responses
        level_cog.db.levels.get_xp = AsyncMock(return_value=1500.0)
        level_cog.db.levels.get_level = AsyncMock(return_value=5)

        # Mock levels service
        level_cog.levels_service.enable_xp_cap = False
        level_cog.levels_service.get_level_progress = Mock(return_value=(300, 500))
        level_cog.levels_service.generate_progress_bar = Mock(return_value="`▰▰▰▱▱` 300/500")

        with patch('tux.modules.levels.level.CONFIG') as mock_config:
            mock_config.SHOW_XP_PROGRESS = True

            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await level_cog.level(ctx, None)

                # Verify database calls
                level_cog.db.levels.get_xp.assert_called_once_with(67890, 12345)
                level_cog.db.levels.get_level.assert_called_once_with(67890, 12345)

                # Verify embed creation
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert call_args['title'] == "Level 5"
                assert "Progress to Next Level" in call_args['description']

                # Verify response
                ctx.send.assert_called_once_with(embed=mock_embed)

    async def test_level_command_other_member(self, level_cog):
        """Test level command for another member."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.send = AsyncMock()

        # Mock target member
        member = Mock()
        member.id = 99999
        member.name = "OtherUser"
        member.display_avatar = Mock()
        member.display_avatar.url = "http://example.com/other_avatar.png"

        # Mock database responses
        level_cog.db.levels.get_xp = AsyncMock(return_value=750.0)
        level_cog.db.levels.get_level = AsyncMock(return_value=3)

        # Mock levels service
        level_cog.levels_service.enable_xp_cap = False

        with patch('tux.modules.levels.level.CONFIG') as mock_config:
            mock_config.SHOW_XP_PROGRESS = False

            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await level_cog.level(ctx, member)

                # Verify database calls for the target member
                level_cog.db.levels.get_xp.assert_called_once_with(99999, 12345)
                level_cog.db.levels.get_level.assert_called_once_with(99999, 12345)

                # Verify embed creation
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert "Level 3" in call_args['description']
                assert "XP: 750" in call_args['description']

    async def test_level_command_max_level_reached(self, level_cog):
        """Test level command when max level is reached."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.author.name = "MaxLevelUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.send = AsyncMock()

        # Mock database responses - user at max level
        level_cog.db.levels.get_xp = AsyncMock(return_value=50000.0)
        level_cog.db.levels.get_level = AsyncMock(return_value=100)

        # Mock levels service with XP cap enabled
        level_cog.levels_service.enable_xp_cap = True
        level_cog.levels_service.max_level = 100
        level_cog.levels_service.calculate_xp_for_level = Mock(return_value=45000.0)

        with patch('tux.modules.levels.level.CONFIG') as mock_config:
            mock_config.SHOW_XP_PROGRESS = False

            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await level_cog.level(ctx, None)

                # Verify embed shows max level and limit reached
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert "Level 100" in call_args['description']
                assert "45000 (limit reached)" in call_args['custom_footer_text']

    async def test_level_command_with_progress_bar(self, level_cog):
        """Test level command with progress bar enabled."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.send = AsyncMock()

        # Mock database responses
        level_cog.db.levels.get_xp = AsyncMock(return_value=2750.0)
        level_cog.db.levels.get_level = AsyncMock(return_value=7)

        # Mock levels service
        level_cog.levels_service.enable_xp_cap = False
        level_cog.levels_service.get_level_progress = Mock(return_value=(250, 400))
        level_cog.levels_service.generate_progress_bar = Mock(return_value="`▰▰▰▰▰▰▱▱▱▱` 250/400")

        with patch('tux.modules.levels.level.CONFIG') as mock_config:
            mock_config.SHOW_XP_PROGRESS = True

            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                await level_cog.level(ctx, None)

                # Verify progress calculation was called
                level_cog.levels_service.get_level_progress.assert_called_once_with(2750.0, 7)
                level_cog.levels_service.generate_progress_bar.assert_called_once_with(250, 400)

                # Verify embed includes progress bar
                mock_create_embed.assert_called_once()
                call_args = mock_create_embed.call_args[1]
                assert call_args['title'] == "Level 7"
                assert "Progress to Next Level" in call_args['description']
                assert "`▰▰▰▰▰▰▱▱▱▱` 250/400" in call_args['description']

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch('tux.modules.levels.level.generate_usage'):
            with patch('tux.modules.levels.level.LevelsService'):
                cog = Level(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, level_cog):
        """Test the string representation of the cog."""
        repr_str = repr(level_cog)
        assert "Level" in repr_str
        assert "injection=" in repr_str
