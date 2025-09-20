"""Unit tests for error handling mixin."""

import pytest
from unittest.mock import MagicMock, patch

from tux.shared.error_mixin import ErrorHandlerMixin
from tux.shared.exceptions import TuxError, TuxDatabaseError


class TestErrorHandlerMixin:
    """Test ErrorHandlerMixin functionality."""

    class MockService(ErrorHandlerMixin):
        """Mock service class using ErrorHandlerMixin."""
        pass

    @pytest.fixture
    def service(self):
        """Create mock service instance."""
        return self.MockService()

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_context")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_exception_safe")
    def test_handle_error_with_generic_exception(
        self, mock_capture, mock_set_tag, mock_set_context, mock_logger, service,
    ):
        """Test handle_error with generic exception."""
        error = ValueError("Test error")
        operation = "test_operation"
        context = {"key": "value"}

        result = service.handle_error(error, operation, context=context)

        # Verify logging
        mock_logger.error.assert_called_once_with(f"❌ {operation} failed: {error}")

        # Verify Sentry context and tags
        mock_set_context.assert_called_once_with("operation_context", context)
        mock_set_tag.assert_any_call("component", "MockService")
        mock_set_tag.assert_any_call("operation", operation)

        # Verify exception capture
        mock_capture.assert_called_once_with(error)

        # Verify return message
        assert result == "An unexpected error occurred. Please try again later."

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_context")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_tux_exception")
    def test_handle_error_with_tux_exception(
        self, mock_capture_tux, mock_set_tag, mock_set_context, mock_logger, service,
    ):
        """Test handle_error with TuxError exception."""
        error = TuxDatabaseError("Database connection failed")
        operation = "database_query"

        result = service.handle_error(error, operation)

        # Verify logging
        mock_logger.error.assert_called_once_with(f"❌ {operation} failed: {error}")

        # Verify Sentry tags
        mock_set_tag.assert_any_call("component", "MockService")
        mock_set_tag.assert_any_call("operation", operation)

        # Verify TuxError-specific capture
        mock_capture_tux.assert_called_once_with(error)

        # Verify return message uses TuxError string
        assert result == str(error)

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_exception_safe")
    def test_handle_error_with_custom_user_message(
        self, mock_capture, mock_set_tag, mock_logger, service,
    ):
        """Test handle_error with custom user message."""
        error = RuntimeError("Internal error")
        operation = "test_operation"
        user_message = "Something went wrong, please try again"

        result = service.handle_error(error, operation, user_message=user_message)

        # Verify custom message is returned
        assert result == user_message

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_exception_safe")
    def test_handle_error_with_different_log_level(
        self, mock_capture, mock_set_tag, mock_logger, service,
    ):
        """Test handle_error with different log level."""
        error = ValueError("Test error")
        operation = "test_operation"

        service.handle_error(error, operation, log_level="warning")

        # Verify warning level logging
        mock_logger.warning.assert_called_once_with(f"❌ {operation} failed: {error}")

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_context")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_exception_safe")
    def test_handle_error_without_context(
        self, mock_capture, mock_set_tag, mock_set_context, mock_logger, service,
    ):
        """Test handle_error without additional context."""
        error = ValueError("Test error")
        operation = "test_operation"

        service.handle_error(error, operation)

        # Verify context is not set when not provided
        mock_set_context.assert_not_called()

        # Verify tags are still set
        mock_set_tag.assert_any_call("component", "MockService")
        mock_set_tag.assert_any_call("operation", operation)

    @patch("tux.shared.error_mixin.logger")
    @patch("tux.shared.error_mixin.set_tag")
    @patch("tux.shared.error_mixin.capture_tux_exception")
    @patch("tux.shared.error_mixin.getattr")
    def test_handle_error_component_name_fallback(
        self, mock_getattr, mock_capture_tux, mock_set_tag, mock_logger, service,
    ):
        """Test handle_error component name fallback."""
        error = TuxError("Test error")
        operation = "test_operation"

        # Mock getattr to return "unknown" for __name__ attribute
        def side_effect(obj, name, default=None):
            if name == "__name__":
                return default
            return getattr(obj, name, default)

        mock_getattr.side_effect = side_effect

        service.handle_error(error, operation)

        # Verify fallback component name
        mock_set_tag.assert_any_call("component", "unknown")
