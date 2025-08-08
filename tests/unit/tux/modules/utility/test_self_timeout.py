"""Unit tests for the SelfTimeout cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import timedelta

from tux.modules.utility.self_timeout import SelfTimeout
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def self_timeout_cog(mock_bot_with_container):
    """Create a SelfTimeout cog instance with mocked dependencies."""
    with patch('tux.modules.utility.self_timeout.generate_usage'):
        return SelfTimeout(mock_bot_with_container)


@pytest.mark.asyncio
class TestSelfTimeoutCog:
    """Test cases for the SelfTimeout cog."""

    async def test_cog_initialization(self, self_timeout_cog):
        """Test that the cog initectly with dependency injection."""
        assert self_timeout_cog.bot is not None
        assert self_timeout_cog.db_service is not None
        assert hasattr(self_timeout_cog, 'db')  # Backward compatibility

    async def test_self_timeout_success_new_timeout(self, self_timeout_cog):
        """Test successful self timeout for user without existing AFK."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.guild.name = "Test Guild"
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.reply = AsyncMock()
        ctx.author.send = AsyncMock()

        # Mock guild member
        mock_member = Mock()
        mock_member.id = 67890
        mock_member.timeout = AsyncMock()
        ctx.guild.get_member = Mock(return_value=mock_member)

        # Mock no existing AFK entry
        self_timeout_cog.db.afk.get_afk_member = AsyncMock(return_value=None)

        # Mock confirmation view
        mock_view = Mock()
        mock_view.value = True  # User confirmed
        mock_view.wait = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):  # 1 hour
            with patch('tux.utils.functions.seconds_to_human_readable', return_value="1 hour"):
                with patch('tux.ui.views.confirmation.ConfirmationDanger', return_value=mock_view):
                    with patch('tux.modules.utility.self_timeout.add_afk', new_callable=AsyncMock) as mock_add_afk:
                        # Mock confirmation message
                        mock_confirmation = Mock()
                        mock_confirmation.delete = AsyncMock()
                        ctx.reply.return_value = mock_confirmation

                        await self_timeout_cog.self_timeout(ctx, "1h", reason="Testing timeout")

                        # Verify confirmation was shown
                        ctx.reply.assert_called_once()
                        mock_view.wait.assert_called_once()
                        mock_confirmation.delete.assert_called_once()

                        # Verify DM was sent
                        ctx.author.send.assert_called_once()
                        dm_content = ctx.author.send.call_args[0][0]
                        assert "timed yourself out" in dm_content
                        assert "Testing timeout" in dm_content

                        # Verify timeout was applied
                        mock_member.timeout.assert_called_once()
                        timeout_args = mock_member.timeout.call_args[0]
                        assert isinstance(timeout_args[0], timedelta)

                        # Verify AFK was added
                        mock_add_afk.assert_called_once()

    async def test_self_timeout_with_existing_afk(self, self_timeout_cog):
        """Test self timeout when user already has AFK status."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.guild.name = "Test Guild"
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.reply = AsyncMock()
        ctx.author.send = AsyncMock()

        # Mock guild member
        mock_member = Mock()
        mock_member.id = 67890
        mock_member.timeout = AsyncMock()
        ctx.guild.get_member = Mock(return_value=mock_member)

        # Mock existing AFK entry
        mock_afk_entry = Mock()
        mock_afk_entry.reason = "Previous AFK reason"
        mock_afk_entry.nickname = "OldNick"
        self_timeout_cog.db.afk.get_afk_member = AsyncMock(return_value=mock_afk_entry)

        # Mock confirmation view
        mock_view = Mock()
        mock_view.value = True  # User confirmed
        mock_view.wait = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):
            with patch('tux.utils.functions.seconds_to_human_readable', return_value="1 hour"):
                with patch('tux.ui.views.confirmation.ConfirmationDanger', return_value=mock_view):
                    with patch('tux.modules.utility.self_timeout.del_afk', new_callable=AsyncMock) as mock_del_afk:
                        with patch('tux.modules.utility.self_timeout.add_afk', new_callable=AsyncMock) as mock_add_afk:
                            # Mock confirmation message
                            mock_confirmation = Mock()
                            mock_confirmation.delete = AsyncMock()
                            ctx.reply.return_value = mock_confirmation

                            # Use default reason to test AFK reason inheritance
                            await self_timeout_cog.self_timeout(ctx, "1h")

                            # Verify existing AFK was removed
                            mock_del_afk.assert_called_once_with(
                                self_timeout_cog.db, mock_member, mock_afk_entry.nickname,
                            )

                            # Verify new AFK was added with inherited reason
                            mock_add_afk.assert_called_once()
                            add_afk_args = mock_add_afk.call_args[0]
                            assert add_afk_args[1] == "Previous AFK reason"  # Inherited reason

    async def test_self_timeout_user_cancels(self, self_timeout_cog):
        """Test self timeout when user cancels confirmation."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.reply = AsyncMock()

        # Mock guild member
        mock_member = Mock()
        ctx.guild.get_member = Mock(return_value=mock_member)

        # Mock no existing AFK entry
        self_timeout_cog.db.afk.get_afk_member = AsyncMock(return_value=None)

        # Mock confirmation view - user cancels
        mock_view = Mock()
        mock_view.value = False  # User cancelled
        mock_view.wait = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):
            with patch('tux.ui.views.confirmation.ConfirmationDanger', return_value=mock_view):
                # Mock confirmation message
                mock_confirmation = Mock()
                mock_confirmation.delete = AsyncMock()
                ctx.reply.return_value = mock_confirmation

                await self_timeout_cog.self_timeout(ctx, "1h", reason="Test")

                # Verify confirmation was shown and deleted
                ctx.reply.assert_called_once()
                mock_view.wait.assert_called_once()
                mock_confirmation.delete.assert_called_once()

                # Verify no timeout was applied (member.timeout not called)
                assert not hasattr(mock_member, 'timeout') or not mock_member.timeout.called

    async def test_self_timeout_invalid_duration(self, self_timeout_cog):
        """Test self timeout with invalid duration."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.reply = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=0):  # Invalid
            await self_timeout_cog.self_timeout(ctx, "invalid", reason="Test")

            # Verify error response
            ctx.reply.assert_called_once()
            call_args = ctx.reply.call_args[0]
            assert "Invalid time format" in call_args[0]

    async def test_self_timeout_duration_too_long(self, self_timeout_cog):
        """Test self timeout with duration longer than 7 days."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.reply = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=604801):  # > 7 days
            await self_timeout_cog.self_timeout(ctx, "8d", reason="Test")

            # Verify error response
            ctx.reply.assert_called_once()
            call_args = ctx.reply.call_args[0]
            assert "cannot be longer than 7 days" in call_args[0]

    async def test_self_timeout_duration_too_short(self, self_timeout_cog):
        """Test self timeout with duration shorter than 5 minutes."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.reply = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=299):  # < 5 minutes
            await self_timeout_cog.self_timeout(ctx, "4m", reason="Test")

            # Verify error response
            ctx.reply.assert_called_once()
            call_args = ctx.reply.call_args[0]
            assert "cannot be less than 5 minutes" in call_args[0]

    async def test_self_timeout_no_guild(self, self_timeout_cog):
        """Test self timeout when not in a guild."""
        # Mock context without guild
        ctx = Mock()
        ctx.guild = None
        ctx.send = AsyncMock()

        await self_timeout_cog.self_timeout(ctx, "1h", reason="Test")

        # Verify error response
        ctx.send.assert_called_once_with("Command must be run in a guild!", ephemeral=True)

    async def test_self_timeout_member_not_found(self, self_timeout_cog):
        """Test self timeout when member is not found in guild."""
        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.guild.get_member = Mock(return_value=None)  # Member not found

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):
            await self_timeout_cog.self_timeout(ctx, "1h", reason="Test")

            # Should return early without doing anything
            ctx.guild.get_member.assert_called_once_with(67890)

    async def test_self_timeout_dm_forbidden_fallback(self, self_timeout_cog):
        """Test self timeout when DM fails, falls back to channel message."""
        import discord

        # Mock context
        ctx = Mock()
        ctx.guild = Mock()
        ctx.guild.id = 12345
        ctx.guild.name = "Test Guild"
        ctx.author = Mock()
        ctx.author.id = 67890
        ctx.reply = AsyncMock()
        ctx.author.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "DMs disabled"))

        # Mock guild member
        mock_member = Mock()
        mock_member.id = 67890
        mock_member.timeout = AsyncMock()
        ctx.guild.get_member = Mock(return_value=mock_member)

        # Mock no existing AFK entry
        self_timeout_cog.db.afk.get_afk_member = AsyncMock(return_value=None)

        # Mock confirmation view
        mock_view = Mock()
        mock_view.value = True
        mock_view.wait = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):
            with patch('tux.utils.functions.seconds_to_human_readable', return_value="1 hour"):
                with patch('tux.ui.views.confirmation.ConfirmationDanger', return_value=mock_view):
                    with patch('tux.modules.utility.self_timeout.add_afk', new_callable=AsyncMock):
                        # Mock confirmation message
                        mock_confirmation = Mock()
                        mock_confirmation.delete = AsyncMock()
                        ctx.reply.return_value = mock_confirmation

                        await self_timeout_cog.self_timeout(ctx, "1h", reason="Test")

                        # Verify DM was attempted
                        ctx.author.send.assert_called_once()

                        # Verify fallback to channel reply
                        assert ctx.reply.call_count == 2  # Confirmation + fallback message

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch('tux.modules.utility.self_timeout.generate_usage'):
            cog = SelfTimeout(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, self_timeout_cog):
        """Test the string representation of the cog."""
        repr_str = repr(self_timeout_cog)
        assert "SelfTimeout" in repr_str
        assert "injection=" in repr_str
