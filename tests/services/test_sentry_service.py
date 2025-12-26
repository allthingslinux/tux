"""Unit tests for Sentry service functions."""

from unittest.mock import MagicMock, patch

import discord
import httpx
import pytest

from tux.services.sentry import (
    capture_database_error,
    capture_exception_safe,
    capture_tux_exception,
    convert_httpx_error,
    set_command_context,
    set_context,
    set_tag,
    set_user_context,
    track_command_end,
    track_command_start,
)
from tux.shared.exceptions import (
    TuxAPIConnectionError,
    TuxAPIPermissionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
    TuxDatabaseError,
    TuxError,
)


class TestSentryCaptureFunctions:
    """Test Sentry capture functions."""

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.sentry_sdk")
    def test_capture_exception_safe_with_generic_exception(
        self,
        mock_sentry_sdk,
        mock_is_initialized,
    ) -> None:
        """Test capture_exception_safe with generic exception."""
        mock_is_initialized.return_value = True
        error = ValueError("Test error")

        capture_exception_safe(error)

        mock_sentry_sdk.capture_exception.assert_called_once_with(error)

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.sentry_sdk")
    def test_capture_exception_safe_when_not_initialized(
        self,
        mock_sentry_sdk,
        mock_is_initialized,
    ) -> None:
        """Test capture_exception_safe when Sentry not initialized."""
        mock_is_initialized.return_value = False
        error = ValueError("Test error")

        capture_exception_safe(error)

        mock_sentry_sdk.capture_exception.assert_not_called()

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.sentry_sdk")
    def test_capture_tux_exception(self, mock_sentry_sdk, mock_is_initialized) -> None:
        """Test capture_tux_exception with TuxError."""
        mock_is_initialized.return_value = True
        error = TuxError("Test Tux error")

        capture_tux_exception(error)

        mock_sentry_sdk.capture_exception.assert_called_once_with(error)

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.sentry_sdk")
    def test_capture_database_error(self, mock_sentry_sdk, mock_is_initialized) -> None:
        """Test capture_database_error with context."""
        mock_is_initialized.return_value = True
        mock_sentry_sdk.push_scope.return_value.__enter__ = MagicMock()
        mock_sentry_sdk.push_scope.return_value.__exit__ = MagicMock()

        error = TuxDatabaseError("Database connection failed")

        capture_database_error(
            error,
            operation="test_query",
            query="SELECT * FROM test",
        )

        mock_sentry_sdk.capture_exception.assert_called_once_with(error)

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.capture_api_error")
    def test_convert_httpx_error_404(
        self,
        mock_capture_api_error,
        mock_is_initialized,
    ) -> None:
        """Test convert_httpx_error with 404 error."""
        mock_is_initialized.return_value = True

        # Mock HTTPStatusError with 404
        mock_response = MagicMock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            "Not Found",
            request=MagicMock(),
            response=mock_response,
        )

        with pytest.raises(TuxAPIResourceNotFoundError) as exc_info:
            convert_httpx_error(
                error,
                service_name="GitHub",
                endpoint="repos.get",
                not_found_resource="test/repo",
            )

        assert exc_info.value.service_name == "GitHub"
        assert exc_info.value.resource_identifier == "test/repo"
        # Should not call capture_api_error for 404 (user error)
        mock_capture_api_error.assert_not_called()

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.capture_api_error")
    def test_convert_httpx_error_403(
        self,
        mock_capture_api_error,
        mock_is_initialized,
    ) -> None:
        """Test convert_httpx_error with 403 error."""
        mock_is_initialized.return_value = True

        # Mock HTTPStatusError with 403
        mock_response = MagicMock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError(
            "Forbidden",
            request=MagicMock(),
            response=mock_response,
        )

        with pytest.raises(TuxAPIPermissionError) as exc_info:
            convert_httpx_error(
                error,
                service_name="GitHub",
                endpoint="repos.get",
            )

        assert exc_info.value.service_name == "GitHub"
        # Should not call capture_api_error for 403 (user error)
        mock_capture_api_error.assert_not_called()

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.capture_api_error")
    def test_convert_httpx_error_500(
        self,
        mock_capture_api_error,
        mock_is_initialized,
    ) -> None:
        """Test convert_httpx_error with 500 error."""
        mock_is_initialized.return_value = True

        # Mock HTTPStatusError with 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        error = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(),
            response=mock_response,
        )

        with pytest.raises(TuxAPIRequestError) as exc_info:
            convert_httpx_error(
                error,
                service_name="GitHub",
                endpoint="repos.get",
            )

        assert exc_info.value.service_name == "GitHub"
        assert exc_info.value.status_code == 500
        # Should call capture_api_error for system errors
        mock_capture_api_error.assert_called_once_with(
            error,
            endpoint="repos.get",
            status_code=500,
        )

    @patch("tux.services.sentry.utils.is_initialized")
    @patch("tux.services.sentry.utils.capture_api_error")
    def test_convert_httpx_error_connection_error(
        self,
        mock_capture_api_error,
        mock_is_initialized,
    ) -> None:
        """Test convert_httpx_error with connection error."""
        mock_is_initialized.return_value = True

        error = httpx.RequestError("Connection failed", request=MagicMock())

        with pytest.raises(TuxAPIConnectionError) as exc_info:
            convert_httpx_error(
                error,
                service_name="GitHub",
                endpoint="repos.get",
            )

        assert exc_info.value.service_name == "GitHub"
        assert exc_info.value.original_error == error
        # Should call capture_api_error for connection errors
        mock_capture_api_error.assert_called_once_with(error, endpoint="repos.get")


class TestSentryContextFunctions:
    """Test Sentry context setting functions."""

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_set_context(self, mock_sentry_sdk, mock_is_initialized) -> None:
        """Test set_context function."""
        mock_is_initialized.return_value = True

        context_data = {"key": "value", "number": 42}
        set_context("test_context", context_data)

        mock_sentry_sdk.set_context.assert_called_once_with(
            "test_context",
            context_data,
        )

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_set_tag(self, mock_sentry_sdk, mock_is_initialized) -> None:
        """Test set_tag function."""
        mock_is_initialized.return_value = True

        set_tag("environment", "test")

        mock_sentry_sdk.set_tag.assert_called_once_with("environment", "test")

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_set_command_context_with_interaction(
        self,
        mock_sentry_sdk,
        mock_is_initialized,
    ) -> None:
        """Test set_command_context with Discord interaction."""
        mock_is_initialized.return_value = True

        # Mock Discord interaction with all required attributes
        mock_interaction = MagicMock(spec=discord.Interaction)
        mock_interaction.id = 123456789
        mock_interaction.guild_id = 987654321
        mock_interaction.channel_id = 555666777
        mock_interaction.type = discord.InteractionType.application_command
        mock_interaction.data = {"name": "test_command"}
        mock_interaction.guild = None
        mock_interaction.channel = None
        mock_interaction.user = None

        set_command_context(mock_interaction)

        # Verify context was set (should call set_context internally)
        mock_sentry_sdk.set_context.assert_called()

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_set_user_context(self, mock_sentry_sdk, mock_is_initialized) -> None:
        """Test set_user_context with Discord user."""
        mock_is_initialized.return_value = True

        # Mock Discord user
        mock_user = MagicMock(spec=discord.User)
        mock_user.id = 123456789
        mock_user.name = "testuser"
        mock_user.display_name = "Test User"
        mock_user.bot = False
        mock_user.system = False

        set_user_context(mock_user)

        # Verify user context was set
        mock_sentry_sdk.set_user.assert_called_once()


class TestSentryPerformanceTracking:
    """Test Sentry performance tracking functions."""

    def test_track_command_start(self) -> None:
        """Test track_command_start function."""
        # This function just records start time, no Sentry calls
        track_command_start("test_command")

        # Should record the start time (no assertions needed for internal state)
        assert True  # Function should complete without error

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_track_command_end_success(
        self,
        mock_sentry_sdk,
        mock_is_initialized,
    ) -> None:
        """Test track_command_end with successful command."""
        mock_is_initialized.return_value = True

        # First start a command to have timing data
        track_command_start("test_command")
        track_command_end("test_command", success=True)

        # Should set success tag
        mock_sentry_sdk.set_tag.assert_any_call("command.success", True)

    @patch("tux.services.sentry.context.is_initialized")
    @patch("tux.services.sentry.context.sentry_sdk")
    def test_track_command_end_failure(
        self,
        mock_sentry_sdk,
        mock_is_initialized,
    ) -> None:
        """Test track_command_end with failed command."""
        mock_is_initialized.return_value = True
        error = ValueError("Test error")

        track_command_start("test_command")
        track_command_end("test_command", success=False, error=error)

        # Should set failure tags
        mock_sentry_sdk.set_tag.assert_any_call("command.success", False)
        mock_sentry_sdk.set_tag.assert_any_call("command.error_type", "ValueError")
