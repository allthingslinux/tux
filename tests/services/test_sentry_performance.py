"""Unit tests for Sentry performance tracking and command monitoring."""

import unittest.mock
from typing import Any
from unittest.mock import MagicMock, patch

import discord
import pytest
from discord.ext import commands

from tux.services.sentry import track_command_end, track_command_start
from tux.services.sentry.cog import SentryHandler
from tux.services.sentry.context import _command_start_times


class TestSentryPerformanceTracking:
    """Test Sentry performance tracking functions."""

    def test_track_command_start_creates_transaction(self) -> None:
        """Test track_command_start records start time."""
        # Clear any existing start times

        _command_start_times.clear()

        track_command_start("test_command")

        # Verify the start time was recorded
        assert "test_command" in _command_start_times
        assert isinstance(_command_start_times["test_command"], float)

    @patch("tux.services.sentry.sentry_sdk")
    def test_track_command_start_when_not_initialized(self, mock_sentry_sdk) -> None:
        """Test track_command_start when Sentry not initialized."""
        mock_sentry_sdk.is_initialized.return_value = False

        track_command_start("test_command")

        mock_sentry_sdk.start_transaction.assert_not_called()

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.set_tag")
    def test_track_command_end_success(self, mock_set_tag, mock_is_initialized) -> None:
        """Test track_command_end with successful command."""
        mock_is_initialized.return_value = True

        # Set up a start time first

        _command_start_times["test_command"] = 1000.0

        track_command_end("test_command", success=True)

        # Verify tags were set
        mock_set_tag.assert_any_call("command.success", True)
        mock_set_tag.assert_any_call("command.execution_time_ms", unittest.mock.ANY)

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.set_tag")
    @patch("tux.services.sentry.context.set_context")
    def test_track_command_end_failure_with_error(
        self,
        mock_set_context,
        mock_set_tag,
        mock_is_initialized,
    ) -> None:
        """Test track_command_end with failed command and error."""
        mock_is_initialized.return_value = True

        # Set up a start time first

        _command_start_times["test_command"] = 1000.0

        error = ValueError("Command failed")
        track_command_end("test_command", success=False, error=error)

        # Verify tags and context were set
        mock_set_tag.assert_any_call("command.success", False)
        mock_set_tag.assert_any_call("command.error_type", "ValueError")
        mock_set_context.assert_called_once()

    @patch("tux.services.sentry.context.is_initialized")
    def test_track_command_end_no_current_span(self, mock_is_initialized) -> None:
        """Test track_command_end when sentry is not initialized."""
        mock_is_initialized.return_value = False

        # Should not raise an error
        track_command_end("test_command", success=True)


class TestSentryHandlerCog:
    """Test SentryHandler cog for command monitoring."""

    @pytest.fixture
    def mock_bot(self):
        """Create mock bot."""
        return MagicMock()

    @pytest.fixture
    def sentry_handler(self, mock_bot: Any):
        """Create SentryHandler instance."""
        return SentryHandler(mock_bot)

    @pytest.mark.asyncio
    @patch("tux.services.sentry.cog.set_command_context")
    @patch("tux.services.sentry.cog.set_user_context")
    @patch("tux.services.sentry.cog.track_command_start")
    async def test_on_command_sets_context_and_tracks(
        self,
        mock_track_start,
        mock_set_user,
        mock_set_command,
        sentry_handler,
    ) -> None:
        """Test on_command sets context and starts tracking."""
        mock_ctx = MagicMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "test_command"
        mock_ctx.author = MagicMock()

        await sentry_handler.on_command(mock_ctx)

        mock_set_command.assert_called_once_with(mock_ctx)
        mock_set_user.assert_called_once_with(mock_ctx.author)
        mock_track_start.assert_called_once_with("test_command")

    @pytest.mark.asyncio
    async def test_on_command_without_command(self, sentry_handler) -> None:
        """Test on_command when context has no command."""
        mock_ctx = MagicMock(spec=commands.Context)
        mock_ctx.command = None

        with patch("tux.services.sentry.cog.track_command_start") as mock_track:
            await sentry_handler.on_command(mock_ctx)
            mock_track.assert_not_called()

    @pytest.mark.asyncio
    @patch("tux.services.sentry.cog.track_command_end")
    async def test_on_command_completion_tracks_success(
        self,
        mock_track_end,
        sentry_handler,
    ) -> None:
        """Test on_command_completion tracks successful completion."""
        mock_ctx = MagicMock()
        mock_ctx.command = MagicMock()
        mock_ctx.command.qualified_name = "test_command"

        await sentry_handler.on_command_completion(mock_ctx)

        mock_track_end.assert_called_once_with("test_command", success=True)

    @pytest.mark.asyncio
    async def test_on_command_completion_without_command(self, sentry_handler) -> None:
        """Test on_command_completion when context has no command."""
        mock_ctx = MagicMock(spec=commands.Context)
        mock_ctx.command = None

        with patch("tux.services.sentry.cog.track_command_end") as mock_track:
            await sentry_handler.on_command_completion(mock_ctx)
            mock_track.assert_not_called()

    @pytest.mark.asyncio
    @patch("tux.services.sentry.cog.set_command_context")
    @patch("tux.services.sentry.cog.set_user_context")
    @patch("tux.services.sentry.cog.track_command_end")
    async def test_on_app_command_completion_sets_context_and_tracks(
        self,
        mock_track_end,
        mock_set_user,
        mock_set_command,
        sentry_handler,
    ) -> None:
        """Test on_app_command_completion sets context and tracks completion."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.command.qualified_name = "test_app_command"
        mock_interaction.user = MagicMock()

        await sentry_handler.on_app_command_completion(mock_interaction)

        mock_set_command.assert_called_once_with(mock_interaction)
        mock_set_user.assert_called_once_with(mock_interaction.user)
        mock_track_end.assert_called_once_with("test_app_command", success=True)

    @pytest.mark.asyncio
    async def test_on_app_command_completion_without_command(
        self,
        sentry_handler,
    ) -> None:
        """Test on_app_command_completion when interaction has no command."""
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.command = None

        with patch("tux.services.sentry.cog.track_command_end") as mock_track:
            await sentry_handler.on_app_command_completion(mock_interaction)
            mock_track.assert_not_called()


class TestCommandPerformanceIntegration:
    """Test command performance tracking integration."""

    @pytest.mark.asyncio
    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.set_tag")
    async def test_full_command_lifecycle_tracking(
        self,
        mock_set_tag,
        mock_is_initialized,
    ) -> None:
        """Test full command lifecycle from start to completion."""
        mock_is_initialized.return_value = True

        # Simulate command lifecycle
        command_name = "test_lifecycle_command"

        # Start tracking
        track_command_start(command_name)

        # Verify start time was recorded

        assert command_name in _command_start_times

        # End tracking successfully
        track_command_end(command_name, success=True)

        # Verify tags were set and start time was removed
        mock_set_tag.assert_any_call("command.success", True)
        assert command_name not in _command_start_times

    @pytest.mark.asyncio
    @patch("tux.services.sentry.context.set_context")
    @patch("tux.services.sentry.context.set_tag")
    @patch("tux.services.sentry.context.is_initialized")
    async def test_command_error_tracking_with_context(
        self,
        mock_is_initialized,
        mock_set_tag,
        mock_set_context,
    ) -> None:
        """Test command error tracking includes proper context."""
        mock_is_initialized.return_value = True

        command_name = "failing_command"
        error = commands.CommandError("Permission denied")

        # Start and fail command
        track_command_start(command_name)
        track_command_end(command_name, success=False, error=error)

        # Verify error context was set
        mock_set_tag.assert_any_call("command.success", False)
        mock_set_tag.assert_any_call("command.error_type", "CommandError")
        mock_set_context.assert_called()

    @pytest.mark.asyncio
    @patch("tux.services.sentry.context.set_tag")
    @patch("tux.services.sentry.context.is_initialized")
    async def test_concurrent_command_tracking(
        self,
        mock_is_initialized,
        mock_set_tag,
    ) -> None:
        """Test tracking multiple concurrent commands."""
        mock_is_initialized.return_value = True

        # Start multiple commands
        track_command_start("command1")
        track_command_start("command2")

        # Complete them in different order
        track_command_end("command2", success=True)
        track_command_end("command1", success=False, error=ValueError("Failed"))

        # Verify both were tracked correctly
        mock_set_tag.assert_any_call("command.success", True)
        mock_set_tag.assert_any_call("command.success", False)
        mock_set_tag.assert_any_call("command.error_type", "ValueError")
