"""Unit tests for the RemindMe cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
import datetime

from tux.cogs.utility.remindme import RemindMe
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def remindme_cog(mock_bot_with_container):
    """Create a RemindMe cog instance with mocked dependencies."""
    with patch('tux.cogs.utility.remindme.generate_usage'):
        cog = RemindMe(mock_bot_with_container)
        return cog


@pytest.mark.asyncio
class TestRemindMeCog:
    """Test cases for the RemindMe cog."""

    async def test_cog_initialization(self, remindme_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert remindme_cog.bot is not None
        assert remindme_cog.db_service is not None
        assert hasattr(remindme_cog, 'db')  # Backward compatibility
        assert remindme_cog._initialized is False

    async def test_send_reminder_success_dm(self, remindme_cog):
        """Test sending reminder via DM successfully."""
        # Mock reminder
        reminder = Mock()
        reminder.reminder_user_id = 12345
        reminder.reminder_content = "Test reminder"
        reminder.reminder_id = 1
        reminder.reminder_channel_id = 67890

        # Mock user
        mock_user = Mock()
        mock_user.name = "TestUser"
        mock_user.display_avatar = Mock()
        mock_user.display_avatar.url = "http://example.com/avatar.png"
        mock_user.send = AsyncMock()

        remindme_cog.bot.get_user = Mock(return_value=mock_user)
        remindme_cog.db.reminder.delete_reminder_by_id = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await remindme_cog.send_reminder(reminder)

            # Verify DM was sent
            mock_user.send.assert_called_once_with(embed=mock_embed)

            # Verify reminder was deleted
            remindme_cog.db.reminder.delete_reminder_by_id.assert_called_once_with(1)

    async def test_send_reminder_dm_forbidden_fallback_channel(self, remindme_cog):
        """Test sending reminder falls back to channel when DM is forbidden."""
        import discord

        # Mock reminder
        reminder = Mock()
        reminder.reminder_user_id = 12345
        reminder.reminder_content = "Test reminder"
        reminder.reminder_id = 1
        reminder.reminder_channel_id = 67890

        # Mock user that raises Forbidden on DM
        mock_user = Mock()
        mock_user.name = "TestUser"
        mock_user.display_avatar = Mock()
        mock_user.display_avatar.url = "http://example.com/avatar.png"
        mock_user.mention = "<@12345>"
        mock_user.send = AsyncMock(side_effect=discord.Forbidden(Mock(), "DMs disabled"))

        # Mock channel
        mock_channel = Mock()
        mock_channel.send = AsyncMock()

        remindme_cog.bot.get_user = Mock(return_value=mock_user)
        remindme_cog.bot.get_channel = Mock(return_value=mock_channel)
        remindme_cog.db.reminder.delete_reminder_by_id = AsyncMock()

        with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
            mock_embed = Mock()
            mock_create_embed.return_value = mock_embed

            await remindme_cog.send_reminder(reminder)

            # Verify fallback to channel
            mock_channel.send.assert_called_once()
            call_args = mock_channel.send.call_args[1]
            assert "Failed to DM you" in call_args['content']
            assert call_args['embed'] == mock_embed

    async def test_send_reminder_user_not_found(self, remindme_cog):
        """Test sending reminder when user is not found."""
        # Mock reminder
        reminder = Mock()
        reminder.reminder_user_id = 12345
        reminder.reminder_content = "Test reminder"
        reminder.reminder_id = 1

        remindme_cog.bot.get_user = Mock(return_value=None)
        remindme_cog.db.reminder.delete_reminder_by_id = AsyncMock()

        with patch('loguru.logger.error') as mock_logger:
            await remindme_cog.send_reminder(reminder)

            # Verify error was logged
            mock_logger.assert_called_once()
            assert "user with ID 12345 not found" in mock_logger.call_args[0][0]

    async def test_on_ready_process_existing_reminders(self, remindme_cog):
        """Test processing existing reminders on bot ready."""
        # Mock existing reminders
        current_time = datetime.datetime.now(datetime.UTC)

        # Expired reminder
        expired_reminder = Mock()
        expired_reminder.reminder_sent = False
        expired_reminder.reminder_expires_at = current_time - datetime.timedelta(hours=1)

        # Future reminder
        future_reminder = Mock()
        future_reminder.reminder_sent = False
        future_reminder.reminder_expires_at = current_time + datetime.timedelta(hours=1)

        # Old sent reminder (should be deleted)
        old_reminder = Mock()
        old_reminder.reminder_sent = True
        old_reminder.reminder_id = 999

        reminders = [expired_reminder, future_reminder, old_reminder]
        remindme_cog.db.reminder.get_all_reminders = AsyncMock(return_value=reminders)
        remindme_cog.db.reminder.delete_reminder_by_id = AsyncMock()

        # Mock send_reminder
        remindme_cog.send_reminder = AsyncMock()

        # Mock loop.call_later
        remindme_cog.bot.loop.call_later = Mock()

        await remindme_cog.on_ready()

        # Verify expired reminder was sent immediately
        remindme_cog.send_reminder.assert_called_once_with(expired_reminder)

        # Verify future reminder was scheduled
        remindme_cog.bot.loop.call_later.assert_called_once()

        # Verify old reminder was deleted
        remindme_cog.db.reminder.delete_reminder_by_id.assert_called_once_with(999)

        # Verify initialization flag was set
        assert remindme_cog._initialized is True

    async def test_on_ready_already_initialized(self, remindme_cog):
        """Test that on_ready doesn't process reminders if already initialized."""
        remindme_cog._initialized = True
        remindme_cog.db.reminder.get_all_reminders = AsyncMock()

        await remindme_cog.on_ready()

        # Should not call database
        remindme_cog.db.reminder.get_all_reminders.assert_not_called()

    async def test_remindme_command_success(self, remindme_cog):
        """Test successful reminder creation."""
        # Mock context
        ctx = Mock()
        ctx.author = Mock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.channel = Mock()
        ctx.channel.id = 67890
        ctx.guild = Mock()
        ctx.guild.id = 11111
        ctx.reply = AsyncMock()

        # Mock reminder object
        mock_reminder = Mock()
        mock_reminder.reminder_id = 1
        remindme_cog.db.reminder.insert_reminder = AsyncMock(return_value=mock_reminder)

        # Mock loop.call_later
        remindme_cog.bot.loop.call_later = Mock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):  # 1 hour
            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_embed.add_field = Mock()
                mock_create_embed.return_value = mock_embed

                await remindme_cog.remindme(ctx, "1h", reminder="Test reminder")

                # Verify reminder was created
                remindme_cog.db.reminder.insert_reminder.assert_called_once()

                # Verify reminder was scheduled
                remindme_cog.bot.loop.call_later.assert_called_once()

                # Verify success response
                ctx.reply.assert_called_once_with(embed=mock_embed, ephemeral=True)

    async def test_remindme_command_invalid_time(self, remindme_cog):
        """Test reminder command with invalid time format."""
        # Mock context
        ctx = Mock()
        ctx.reply = AsyncMock()

        with patch('tux.utils.functions.convert_to_seconds', return_value=0):  # Invalid time
            await remindme_cog.remindme(ctx, "invalid", reminder="Test")

            # Verify error response
            ctx.reply.assert_called_once()
            call_args = ctx.reply.call_args[0]
            assert "Invalid time format" in call_args[0]

    async def test_remindme_command_database_error(self, remindme_cog):
        """Test reminder command when database insertion fails."""
        # Mock context
        ctx = Mock()
        ctx.author = Mock()
        ctx.author.id = 12345
        ctx.author.name = "TestUser"
        ctx.author.display_avatar = Mock()
        ctx.author.display_avatar.url = "http://example.com/avatar.png"
        ctx.channel = Mock()
        ctx.channel.id = 67890
        ctx.guild = Mock()
        ctx.guild.id = 11111
        ctx.reply = AsyncMock()

        # Mock database error
        remindme_cog.db.reminder.insert_reminder = AsyncMock(
            side_effect=Exception("Database error"),
        )

        with patch('tux.utils.functions.convert_to_seconds', return_value=3600):
            with patch('tux.ui.embeds.EmbedCreator.create_embed') as mock_create_embed:
                mock_embed = Mock()
                mock_create_embed.return_value = mock_embed

                with patch('loguru.logger.error') as mock_logger:
                    await remindme_cog.remindme(ctx, "1h", reminder="Test")

                    # Verify error was logged
                    mock_logger.assert_called_once()

                    # Verify error response
                    ctx.reply.assert_called_once_with(embed=mock_embed, ephemeral=True)

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch('tux.cogs.utility.remindme.generate_usage'):
            cog = RemindMe(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, remindme_cog):
        """Test the string representation of the cog."""
        repr_str = repr(remindme_cog)
        assert "RemindMe" in repr_str
        assert "injection=" in repr_str
