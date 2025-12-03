"""End-to-end integration tests for error handling flow."""

import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from discord import app_commands
from discord.ext import commands

from tux.services.handlers.error.cog import ErrorHandler
from tux.shared.exceptions import TuxError, TuxPermissionDeniedError


class TestErrorHandlingEndToEnd:
    """Test complete error handling flow from command to user response."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot."""
        bot = MagicMock()
        return bot

    @pytest.fixture
    def error_handler(self, mock_bot):
        """Create ErrorHandler cog."""
        return ErrorHandler(mock_bot)

    @pytest.mark.asyncio
    async def test_command_error_sends_user_response(self, error_handler):
        """Test that CommandError results in user response."""
        # Setup mock context
        mock_ctx = MagicMock()
        mock_ctx.reply = AsyncMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "test_command"
        mock_ctx.command.has_error_handler.return_value = False
        mock_ctx.cog = None

        error = commands.CommandError("Test error message")

        # Handle error
        await error_handler.on_command_error(mock_ctx, error)

        # Verify user got a response
        mock_ctx.reply.assert_called_once()
        call_args = mock_ctx.reply.call_args
        assert "embed" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_tux_error_shows_custom_message(self, error_handler):
        """Test that TuxError shows default message (not custom)."""
        mock_ctx = MagicMock()
        mock_ctx.reply = AsyncMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "test_command"
        mock_ctx.command.has_error_handler.return_value = False
        mock_ctx.cog = None

        error = TuxError("Custom error message")

        await error_handler.on_command_error(mock_ctx, error)

        # Verify response was sent (TuxError uses default message)
        mock_ctx.reply.assert_called_once()
        call_args = mock_ctx.reply.call_args
        embed = call_args.kwargs["embed"]
        assert "An unexpected error occurred" in str(embed.description)

    @pytest.mark.asyncio
    async def test_app_command_error_sends_response(self, error_handler):
        """Test that app command errors send responses."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        mock_interaction.response.is_done.return_value = False
        mock_interaction.command = MagicMock()
        mock_interaction.command.qualified_name = "test_slash"

        error = app_commands.AppCommandError("App command failed")

        await error_handler.on_app_command_error(mock_interaction, error)

        # Verify interaction got a response
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "embed" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_permission_denied_unconfigured_command(self, error_handler):
        """Test that unconfigured command shows helpful setup message."""
        mock_ctx = MagicMock()
        mock_ctx.reply = AsyncMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "dev clear_tree"
        mock_ctx.command.has_error_handler.return_value = False
        mock_ctx.cog = None

        # Mock bot and guild for prefix manager access
        mock_bot = MagicMock()
        mock_prefix_manager = MagicMock()
        mock_prefix_manager._prefix_cache = {123456789: "$"}  # Mock prefix cache
        mock_bot.prefix_manager = mock_prefix_manager

        mock_guild = MagicMock()
        mock_guild.id = 123456789
        mock_ctx.bot = mock_bot
        mock_ctx.guild = mock_guild

        # Simulate unconfigured command (both ranks are 0)
        error = TuxPermissionDeniedError(
            required_rank=0,
            user_rank=0,
            command_name="dev clear_tree",
        )

        await error_handler.on_command_error(mock_ctx, error)

        # Verify response was sent with configuration instructions
        mock_ctx.reply.assert_called_once()
        call_args = mock_ctx.reply.call_args
        embed = call_args.kwargs["embed"]
        description = str(embed.description)

        # Check for key phrases in the message
        assert "not been configured yet" in description
        assert "/config overview" in description
        assert "configure command permissions" in description
        assert "dev clear_tree" in description

    @pytest.mark.asyncio
    async def test_permission_denied_insufficient_rank(self, error_handler):
        """Test that insufficient rank shows clear rank requirement."""
        mock_ctx = MagicMock()
        mock_ctx.reply = AsyncMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "ban"
        mock_ctx.command.has_error_handler.return_value = False
        mock_ctx.cog = None

        # Simulate insufficient rank
        error = TuxPermissionDeniedError(
            required_rank=5,
            user_rank=2,
            command_name="ban",
        )

        await error_handler.on_command_error(mock_ctx, error)

        # Verify response was sent with rank information
        mock_ctx.reply.assert_called_once()
        call_args = mock_ctx.reply.call_args
        embed = call_args.kwargs["embed"]
        description = str(embed.description)

        # Check for key information in the message
        assert "permission rank" in description.lower()
        assert "5" in description  # Required rank
        assert "2" in description  # User's rank
        assert "ban" in description

    @pytest.mark.asyncio
    async def test_permission_denied_app_command(self, error_handler):
        """Test that permission denied works with app commands."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.send_message = AsyncMock()
        mock_interaction.followup.send = AsyncMock()
        mock_interaction.response.is_done.return_value = False
        mock_interaction.command = MagicMock()
        mock_interaction.command.qualified_name = "config"

        # Simulate permission denied for slash command
        error = TuxPermissionDeniedError(
            required_rank=3,
            user_rank=1,
            command_name="config",
        )

        await error_handler.on_app_command_error(mock_interaction, error)

        # Verify interaction got ephemeral response
        mock_interaction.response.send_message.assert_called_once()
        call_args = mock_interaction.response.send_message.call_args
        assert "embed" in call_args.kwargs
        assert call_args.kwargs["ephemeral"] is True

        # Verify message content
        embed = call_args.kwargs["embed"]
        description = str(embed.description)
        assert "3" in description  # Required rank
        assert "1" in description  # User's rank
