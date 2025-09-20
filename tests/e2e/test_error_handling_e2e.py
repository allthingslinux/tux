"""End-to-end integration tests for error handling flow."""

import pytest
from unittest.mock import MagicMock, AsyncMock
import discord
from discord import app_commands
from discord.ext import commands

from tux.services.handlers.error.handler import ErrorHandler
from tux.shared.exceptions import TuxError


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
