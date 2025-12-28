"""Error handler cog unit tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.services.handlers.error.cog import ErrorHandler
from tux.services.handlers.error.config import ErrorHandlerConfig
from tux.shared.exceptions import TuxPermissionError


class TestErrorHandler:
    """Test ErrorHandler cog."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot."""
        bot = MagicMock()
        bot.tree = MagicMock()
        return bot

    @pytest.fixture
    def error_handler(self, mock_bot: Any):
        """Create ErrorHandler instance."""
        return ErrorHandler(mock_bot)

    @pytest.mark.asyncio
    async def test_cog_load_sets_tree_error_handler(
        self,
        error_handler,
        mock_bot,
    ) -> None:
        """Test that cog_load sets the tree error handler."""
        original_handler = MagicMock()
        mock_bot.tree.on_error = original_handler

        await error_handler.cog_load()

        assert error_handler._old_tree_error == original_handler
        assert mock_bot.tree.on_error == error_handler.on_app_command_error

    @pytest.mark.asyncio
    async def test_cog_unload_restores_tree_error_handler(
        self,
        error_handler,
        mock_bot,
    ) -> None:
        """Test that cog_unload restores the original tree error handler."""
        original_handler = MagicMock()
        error_handler._old_tree_error = original_handler

        await error_handler.cog_unload()

        assert mock_bot.tree.on_error == original_handler

    def test_get_error_config_exact_match(self, error_handler) -> None:
        """Test _get_error_config with exact error type match."""
        error = commands.CommandNotFound()
        config = error_handler._get_error_config(error)

        assert isinstance(config, ErrorHandlerConfig)

    def test_get_error_config_parent_class_match(self, error_handler) -> None:
        """Test _get_error_config with parent class match."""
        error = TuxPermissionError("test")
        config = error_handler._get_error_config(error)

        assert isinstance(config, ErrorHandlerConfig)

    def test_get_error_config_default(self, error_handler) -> None:
        """Test _get_error_config returns default for unknown error."""
        error = RuntimeError("Unknown error")
        config = error_handler._get_error_config(error)

        assert isinstance(config, ErrorHandlerConfig)
        assert config.send_to_sentry is True

    @patch("tux.services.handlers.error.cog.logger")
    def test_log_error_with_sentry(self, mock_logger, error_handler) -> None:
        """Test _log_error with Sentry enabled."""
        error = ValueError("Test error")
        config = ErrorHandlerConfig(send_to_sentry=True, log_level="ERROR")

        error_handler._log_error(error, config)

        mock_logger.error.assert_called_once()

    @patch("tux.services.handlers.error.cog.logger")
    def test_log_error_without_sentry(self, mock_logger, error_handler) -> None:
        """Test _log_error with Sentry disabled."""
        error = ValueError("Test error")
        config = ErrorHandlerConfig(send_to_sentry=False, log_level="INFO")

        error_handler._log_error(error, config)

        mock_logger.info.assert_called_once()

    @patch("tux.services.handlers.error.cog.set_command_context")
    @patch("tux.services.handlers.error.cog.set_user_context")
    @patch("tux.services.handlers.error.cog.track_command_end")
    def test_set_sentry_context_with_interaction(
        self,
        mock_track_end,
        mock_set_user,
        mock_set_command,
        error_handler,
    ) -> None:
        """Test _set_sentry_context with Discord interaction."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.command.qualified_name = "test_command"
        mock_interaction.user = MagicMock()
        error = ValueError("Test error")

        error_handler._set_sentry_context(mock_interaction, error)

        mock_set_command.assert_called_once_with(mock_interaction)
        mock_set_user.assert_called_once_with(mock_interaction.user)
        mock_track_end.assert_called_once_with(
            "test_command",
            success=False,
            error=error,
        )

    @patch("tux.services.handlers.error.cog.set_command_context")
    @patch("tux.services.handlers.error.cog.set_user_context")
    @patch("tux.services.handlers.error.cog.track_command_end")
    def test_set_sentry_context_with_context(
        self,
        mock_track_end,
        mock_set_user,
        mock_set_command,
        error_handler,
    ) -> None:
        """Test _set_sentry_context with command context."""
        mock_ctx = MagicMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "test_command"
        mock_ctx.author = MagicMock()
        error = ValueError("Test error")

        error_handler._set_sentry_context(mock_ctx, error)

        mock_set_command.assert_called_once_with(mock_ctx)
        mock_set_user.assert_called_once_with(mock_ctx.author)
        mock_track_end.assert_called_once_with(
            "test_command",
            success=False,
            error=error,
        )

    @pytest.mark.asyncio
    async def test_send_error_response_interaction_not_responded(
        self,
        error_handler,
    ) -> None:
        """Test _send_error_response with interaction that hasn't responded."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.is_done.return_value = False
        mock_interaction.response.send_message = AsyncMock()

        embed = MagicMock(spec=discord.Embed)

        await error_handler._send_error_response(mock_interaction, embed)

        mock_interaction.response.send_message.assert_called_once_with(
            embed=embed,
            ephemeral=True,
        )

    @pytest.mark.asyncio
    async def test_send_error_response_interaction_already_responded(
        self,
        error_handler,
    ) -> None:
        """Test _send_error_response with interaction that already responded."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.response.is_done.return_value = True
        mock_interaction.followup.send = AsyncMock()

        embed = MagicMock(spec=discord.Embed)

        await error_handler._send_error_response(mock_interaction, embed)

        mock_interaction.followup.send.assert_called_once_with(
            embed=embed,
            ephemeral=True,
        )

    @pytest.mark.asyncio
    async def test_send_error_response_context_with_deletion(
        self,
        error_handler,
    ) -> None:
        """Test _send_error_response with context."""
        mock_ctx = MagicMock()
        mock_ctx.reply = AsyncMock()

        embed = MagicMock(spec=discord.Embed)

        await error_handler._send_error_response(mock_ctx, embed)

        mock_ctx.reply.assert_called_once_with(
            embed=embed,
            mention_author=False,
        )

    @pytest.mark.asyncio
    async def test_on_command_error_command_not_found(self, error_handler) -> None:
        """Test on_command_error with CommandNotFound."""
        mock_ctx = MagicMock()
        error = commands.CommandNotFound()

        with patch.object(
            error_handler.suggester,
            "handle_command_not_found",
        ) as mock_suggest:
            await error_handler.on_command_error(mock_ctx, error)
            mock_suggest.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    async def test_on_command_error_skips_if_command_has_handler(
        self,
        error_handler,
    ) -> None:
        """Test on_command_error skips if command has local error handler."""
        mock_ctx = MagicMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.has_error_handler.return_value = True
        error = commands.CommandError()

        with patch.object(error_handler, "_handle_error") as mock_handle:
            await error_handler.on_command_error(mock_ctx, error)
            mock_handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_command_error_skips_if_cog_has_handler(
        self,
        error_handler,
    ) -> None:
        """Test on_command_error skips if cog has local error handler."""
        mock_ctx = MagicMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.has_error_handler.return_value = False
        mock_ctx.cog = MagicMock()
        mock_ctx.cog.has_error_handler.return_value = True
        error = commands.CommandError()

        with patch.object(error_handler, "_handle_error") as mock_handle:
            await error_handler.on_command_error(mock_ctx, error)
            mock_handle.assert_not_called()

    @pytest.mark.asyncio
    async def test_on_app_command_error(self, error_handler) -> None:
        """Test on_app_command_error calls _handle_error."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        error = discord.app_commands.AppCommandError()

        with patch.object(error_handler, "_handle_error") as mock_handle:
            await error_handler.on_app_command_error(mock_interaction, error)
            mock_handle.assert_called_once_with(mock_interaction, error)
