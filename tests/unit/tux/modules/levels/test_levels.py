"""Unit tests for the Levels cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import datetime

from tux.modules.levels.levels import Levels
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def levels_cog(mock_bot_with_container):
    """Create a Levels cog instance with mocked dependencies."""
    with patch('tux.modules.levels.levels.generate_usage'):
        with patch('tux.modules.levels.levels.LevelsService') as mock_levels_service:
            mock_service_instance = Mock()
            mock_levels_service.return_value = mock_service_instance
            cog = Levels(mock_bot_with_container)
            cog.levels_service = mock_service_instance
            return cog


@pytest.mark.asyncio
class TestLevelsCog:
    """Test cases for the Levels cog."""

    async def test_cog_initialization(self, levels_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert levels_cog.bot is not None
        assert levels_cog.db_service is not None
        assert hasattr(levels_cog, 'db')  # Backward compatibility
        assert hasattr(levels_cog, 'levels_service')

    async def test_levels_group_command(self, levels_cog):
        """Test the levels group command shows help when no subcommand is invoked."""
        # Mock context
        ctx = Mock()
        ctx.invoked_subcommand = None
        ctx.send_help = AsyncMock()

        await levels_cog.levels(ctx)

        ctx.send_help.assert_called_once_with("levels")

    async def test_set_level_command_success(self, levels_cog):
        """Test successful level setting."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()
        member.id = 67890
        member.__str__ = Mock(return_value="TestUser#1234")

        # Mock database responses
        levels_cog.db.levels.get_level = AsyncMock(return_value=5)
        levels_cog.db.levels.get_xp = AsyncMock(return_value=1500.0)
        levels_cog.db.levels.update_xp_and_level = AsyncMock()

        # Mock levels service
        levels_cog.levels_service.valid_xplevel_input = Mock(return_value=None)  # Valid input
        levels_cog.levels_service.calculate_xp_for_level = Mock(return_value=2500.0)
        levels_cog.levels_service.update_roles = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await levels_cog.set(ctx, member, 10)

            # Verify validation was called
            levels_cog.levels_service.valid_xplevel_input.assert_called_once_with(10)

            # Verify XP calculation
            levels_cog.levels_service.cap_for_level.assert_called_once_with(10)

            # Verify database update
            levels_cog.db.levels.update_xp_and_level.assert_called_once()
            update_args = levels_cog.db.levels.update_xp_and_level.call_args[0]
            assert update_args[0] == 67890  # member_id
            assert update_args[1] == 12345  # guild_id
            assert update_args[2] == 2500.0  # new_xp
            assert update_args[3] == 10  # new_level

            # Verify roles were updated
            levels_cog.levels_service.update_roles.assert_called_once_with(member, ctx.guild, 10)

            # Verify response
            ctx.send.assert_called_once_with(embed=mock_embed)

    async def test_set_level_command_invalid_input(self, levels_cog):
        """Test level setting with invalid input."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()

        # Mock levels service to return validation error
        mock_error_embed = Mock()
        levels_cog.levels_service.valid_xplevel_input = Mock(return_value=mock_error_embed)

        await levels_cog.set(ctx, member, -5)

        # Verify validation was called
        levels_cog.levels_service.valid_xplevel_input.assert_called_once_with(-5)

        # Verify error response
        ctx.send.assert_called_once_with(embed=mock_error_embed)

    async def test_set_xp_command_success(self, levels_cog):
        """Test successful XP setting."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()
        member.id = 67890
        member.__str__ = Mock(return_value="TestUser#1234")

        # Mock database responses
        levels_cog.db.levels.get_level = AsyncMock(return_value=5)
        levels_cog.db.levels.get_xp = AsyncMock(return_value=1500.0)
        levels_cog.db.levels.update_xp_and_level = AsyncMock()

        # Mock levels service
        levels_cog.levels_service.valid_xplevel_input = Mock(return_value=None)  # Valid input
        levels_cog.levels_service.calculate_level = Mock(return_value=8)
        levels_cog.levels_service.update_roles = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await levels_cog.set_xp(ctx, member, 3000)

            # Verify validation was called
            levels_cog.levels_service.valid_xplevel_input.assert_called_once_with(3000)

            # Verify level calculation
            levels_cog.levels_service.calculate_level.assert_called_once_with(3000)

            # Verify database update
            levels_cog.db.levels.update_xp_and_level.assert_called_once()
            update_args = levels_cog.db.levels.update_xp_and_level.call_args[0]
            assert update_args[0] == 67890  # member_id
            assert update_args[1] == 12345  # guild_id
            assert update_args[2] == 3000.0  # new_xp
            assert update_args[3] == 8  # new_level

            # Verify roles were updated
            levels_cog.levels_service.update_roles.assert_called_once_with(member, ctx.guild, 8)

            # Verify response
            ctx.send.assert_called_once_with(embed=mock_embed)

    async def test_reset_command_success(self, levels_cog):
        """Test successful XP reset."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()
        member.id = 67890
        member.__str__ = Mock(return_value="TestUser#1234")

        # Mock database responses
        levels_cog.db.levels.get_xp = AsyncMock(return_value=2500.0)
        levels_cog.db.levels.reset_xp = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await levels_cog.reset(ctx, member)

            # Verify database calls
            levels_cog.db.levels.get_xp.assert_called_once_with(67890, 12345)
            levels_cog.db.levels.reset_xp.assert_called_once_with(67890, 12345)

            # Verify response
            ctx.send.assert_called_once_with(embed=mock_embed)
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert "XP Reset" in call_args['title']
            assert "reset from **2500** to **0**" in call_args['description']

    async def test_blacklist_command_success(self, levels_cog):
        """Test successful blacklist toggle."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()
        member.id = 67890
        member.__str__ = Mock(return_value="TestUser#1234")

        # Mock database response - user gets blacklisted
        levels_cog.db.levels.toggle_blacklist = AsyncMock(return_value=True)

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await levels_cog.blacklist(ctx, member)

            # Verify database call
            levels_cog.db.levels.toggle_blacklist.assert_called_once_with(67890, 12345)

            # Verify response
            ctx.send.assert_called_once_with(embed=mock_embed)
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert "XP Blacklist" in call_args['title']
            assert "blacklisted" in call_args['description']

    async def test_blacklist_command_unblacklist(self, levels_cog):
        """Test successful blacklist removal."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.send = AsyncMock()

        # Mock member
        member = Mock()
        member.id = 67890
        member.__str__ = Mock(return_value="TestUser#1234")

        # Mock database response - user gets unblacklisted
        levels_cog.db.levels.toggle_blacklist = AsyncMock(return_value=False)

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await levels_cog.blacklist(ctx, member)

            # Verify database call
            levels_cog.db.levels.toggle_blacklist.assert_called_once_with(67890, 12345)

            # Verify response
            ctx.send.assert_called_once_with(embed=mock_embed)
            mock_create_embed.assert_called_once()
            call_args = mock_create_embed.call_args[1]
            assert "XP Blacklist" in call_args['title']
            assert "unblacklisted" in call_args['description']

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch('tux.modules.levels.levels.generate_usage'):
            with patch('tux.modules.levels.levels.LevelsService'):
                cog = Levels(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, levels_cog):
        """Test the string representation of the cog."""
        repr_str = repr(levels_cog)
        assert "Levels" in repr_str
        assert "injection=" in repr_str
