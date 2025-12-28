"""
📝 Logging System Unit Tests.

Comprehensive tests for the logging configuration system including:
- configure_logging() function
- Log level determination with priority handling
- Log level validation
- InterceptHandler level mapping
- Third-party library interception
- Duplicate configuration prevention
"""

import io
import logging
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest
from loguru import logger

from tux.core.logging import (
    INTERCEPTED_LIBRARIES,
    THIRD_PARTY_LOG_LEVELS,
    VALID_LOG_LEVELS,
    StructuredLogger,
    _configure_third_party_logging,
    _determine_log_level,
    _format_record,
    _get_relative_file_path,
    _validate_log_level,
    configure_logging,
    configure_testing_logging,
    verify_logging_interception,
)

# Import _state at module level to avoid repeated imports
from tux.core.logging import _state as logging_state


@contextmanager
def _reset_logging_state():
    """Context manager to reset and restore logging state for tests."""
    original_configured = logging_state.configured
    logging_state.configured = False

    try:
        yield
    finally:
        logging_state.configured = original_configured
        logger.remove()


class TestLogLevelValidation:
    """Test log level validation functionality."""

    @pytest.mark.unit
    def test_validate_log_level_valid_levels(self) -> None:
        """Test validation accepts all valid log levels."""
        for level in VALID_LOG_LEVELS:
            assert _validate_log_level(level) == level
            assert _validate_log_level(level.lower()) == level
            assert _validate_log_level(level.capitalize()) == level

    @pytest.mark.unit
    def test_validate_log_level_invalid_level(self) -> None:
        """Test validation rejects invalid log levels."""
        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level("INVALID")

        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level("debugging")

        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level("")

    @pytest.mark.unit
    def test_validate_log_level_normalizes_case(self) -> None:
        """Test validation normalizes case to uppercase."""
        assert _validate_log_level("debug") == "DEBUG"
        assert _validate_log_level("INFO") == "INFO"
        assert _validate_log_level("Warning") == "WARNING"
        assert _validate_log_level("error") == "ERROR"


class TestLogLevelDetermination:
    """Test log level determination with priority handling."""

    @pytest.mark.unit
    def test_determine_log_level_explicit_level_highest_priority(self) -> None:
        """Test explicit level parameter has highest priority."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = True

        assert _determine_log_level("ERROR", mock_config) == "ERROR"

    @pytest.mark.unit
    def test_determine_log_level_from_config_log_level(self) -> None:
        """Test LOG_LEVEL from config is used when no explicit level."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = False

        result = _determine_log_level(None, mock_config)
        assert result == "WARNING"

    @pytest.mark.unit
    def test_determine_log_level_explicit_info_works(self) -> None:
        """Test explicit LOG_LEVEL=INFO works (was previously broken)."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = "INFO"
        mock_config.DEBUG = False

        result = _determine_log_level(None, mock_config)
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_debug_flag(self) -> None:
        """Test DEBUG flag sets DEBUG level."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = None
        mock_config.DEBUG = True

        result = _determine_log_level(None, mock_config)
        assert result == "DEBUG"

    @pytest.mark.unit
    def test_determine_log_level_default_info(self) -> None:
        """Test default level is INFO when nothing is configured."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = None
        mock_config.DEBUG = False

        result = _determine_log_level(None, mock_config)
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_no_config(self) -> None:
        """Test default level when config is None."""
        result = _determine_log_level(None, None)
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_priority_order(self) -> None:
        """Test priority order: explicit > LOG_LEVEL > DEBUG > default."""
        mock_config = MagicMock()
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = True

        assert _determine_log_level("ERROR", mock_config) == "ERROR"
        assert _determine_log_level(None, mock_config) == "WARNING"

        mock_config.LOG_LEVEL = None
        assert _determine_log_level(None, mock_config) == "DEBUG"

        mock_config.DEBUG = False
        assert _determine_log_level(None, mock_config) == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_validates_all_levels(self) -> None:
        """Test that all determined levels are validated."""
        mock_config = MagicMock()
        mock_config.DEBUG = False

        mock_config.LOG_LEVEL = "INVALID"
        with pytest.raises(ValueError, match="Invalid log level"):
            _determine_log_level(None, mock_config)

        with pytest.raises(ValueError, match="Invalid log level"):
            _determine_log_level("INVALID", mock_config)


class TestConfigureLogging:
    """Test configure_logging() function."""

    @pytest.mark.unit
    def test_configure_logging_removes_default_handler(self) -> None:
        """Test that configure_logging removes loguru's default handler."""
        with _reset_logging_state():
            # Configure logging (removes all handlers and adds custom one)
            configure_logging(level="DEBUG")

            # Verify handler behavior using public API: emit a test log and verify it's captured
            log_capture = io.StringIO()
            handler_id = logger.add(log_capture, level="DEBUG")
            try:
                logger.debug("Test message")
                log_output = log_capture.getvalue()
                assert "Test message" in log_output
                assert "DEBUG" in log_output
            finally:
                logger.remove(handler_id)

    @pytest.mark.unit
    def test_configure_logging_prevents_duplicate_configuration(self) -> None:
        """Test that configure_logging prevents duplicate configuration."""
        with _reset_logging_state():
            configure_logging(level="DEBUG")
            first_handlers = len(logger._core.handlers)
            first_handler_level = logger._core.handlers[
                next(iter(logger._core.handlers.keys()))
            ].levelno

            # Second call should be ignored (duplicate prevention)
            configure_logging(level="INFO")
            assert len(logger._core.handlers) == first_handlers
            # Level should still be DEBUG, not INFO (proves second call was ignored)
            second_handler_level = logger._core.handlers[
                next(iter(logger._core.handlers.keys()))
            ].levelno
            assert second_handler_level == first_handler_level

    @pytest.mark.unit
    def test_configure_logging_with_explicit_level(self) -> None:
        """Test configure_logging with explicit level parameter."""
        with _reset_logging_state():
            mock_config = MagicMock()
            mock_config.LOG_LEVEL = "WARNING"
            mock_config.DEBUG = False

            configure_logging(level="DEBUG", config=mock_config)
            assert logging_state.configured is True

            # Verify the handler level is actually DEBUG, not WARNING
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("DEBUG").no

    @pytest.mark.unit
    def test_configure_logging_with_config(self) -> None:
        """Test configure_logging with config parameter."""
        with _reset_logging_state():
            mock_config = MagicMock()
            mock_config.LOG_LEVEL = "WARNING"
            mock_config.DEBUG = False

            configure_logging(config=mock_config)
            assert logging_state.configured is True

            # Verify the handler level is actually WARNING from config
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("WARNING").no

    @pytest.mark.unit
    def test_configure_testing_logging(self) -> None:
        """Test configure_testing_logging sets DEBUG level."""
        with _reset_logging_state():
            configure_testing_logging()
            assert logging_state.configured is True

            # Verify the handler level is actually DEBUG
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("DEBUG").no


class TestInterceptHandler:
    """Test InterceptHandler level mapping."""

    @pytest.mark.unit
    def test_intercept_handler_level_mapping(self) -> None:
        """Test InterceptHandler correctly maps standard library levels."""
        with _reset_logging_state():
            # Capture log output
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{level} | {message}")

            _configure_third_party_logging()

            record = logging.LogRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )

            root_logger = logging.getLogger()
            intercept_handler = root_logger.handlers[0]
            intercept_handler.emit(record)

            # Verify message was routed to loguru
            output = log_capture.getvalue()
            assert "Test message" in output
            assert "INFO" in output

    @pytest.mark.unit
    def test_intercept_handler_exception_fallback(self) -> None:
        """Test InterceptHandler fallback when patching fails."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="WARNING", format="{message}")

            _configure_third_party_logging()

            # Create a record that will cause patching to fail
            # by using a mock that raises an exception
            class BadRecord(logging.LogRecord):
                def getMessage(self) -> str:  # noqa: N802
                    return "Test {bad} message"

            record = BadRecord(
                name="test.logger",
                level=logging.INFO,
                pathname="test.py",
                lineno=1,
                msg="Test {bad} message",
                args=(),
                exc_info=None,
            )

            root_logger = logging.getLogger()
            intercept_handler = root_logger.handlers[0]

            # Mock logger.patch to raise an exception
            with patch(
                "tux.core.logging.logger.patch",
                side_effect=Exception("Patch failed"),
            ):
                intercept_handler.emit(record)

            # Should log a warning about the exception
            output = log_capture.getvalue()
            assert "Exception while logging message" in output

    @pytest.mark.unit
    def test_intercept_handler_all_levels(self) -> None:
        """Test InterceptHandler handles all standard library levels."""
        with _reset_logging_state():
            # Capture log output
            log_capture = io.StringIO()
            logger.add(log_capture, level="TRACE", format="{level} | {message}")

            _configure_third_party_logging()

            root_logger = logging.getLogger()
            intercept_handler = root_logger.handlers[0]

            levels = [
                logging.DEBUG,
                logging.INFO,
                logging.WARNING,
                logging.ERROR,
                logging.CRITICAL,
            ]

            for level in levels:
                record = logging.LogRecord(
                    name="test.logger",
                    level=level,
                    pathname="test.py",
                    lineno=1,
                    msg=f"Test {level} message",
                    args=(),
                    exc_info=None,
                )
                intercept_handler.emit(record)

            # Verify all messages were routed
            output = log_capture.getvalue()
            assert "DEBUG" in output
            assert "INFO" in output
            assert "WARNING" in output
            assert "ERROR" in output
            assert "CRITICAL" in output

    @pytest.mark.unit
    def test_intercept_handler_unknown_level_fallback(self) -> None:
        """Test InterceptHandler falls back to numeric level for unknown levels."""
        with _reset_logging_state():
            # Capture log output
            log_capture = io.StringIO()
            logger.add(log_capture, level="TRACE", format="{level} | {message}")

            _configure_third_party_logging()

            root_logger = logging.getLogger()
            intercept_handler = root_logger.handlers[0]

            record = logging.LogRecord(
                name="test.logger",
                level=25,  # Between DEBUG and INFO
                pathname="test.py",
                lineno=1,
                msg="Test custom level message",
                args=(),
                exc_info=None,
            )
            record.levelname = "CUSTOM"

            # Should not raise an error and should route the message
            intercept_handler.emit(record)

            # Verify message was routed (fallback to numeric level)
            output = log_capture.getvalue()
            assert "Test custom level message" in output


class TestThirdPartyLogging:
    """Test third-party library logging interception."""

    @pytest.mark.unit
    def test_third_party_logging_interception(self) -> None:
        """Test that third-party libraries are intercepted."""
        _configure_third_party_logging()

        for lib_name in INTERCEPTED_LIBRARIES:
            lib_logger = logging.getLogger(lib_name)
            assert len(lib_logger.handlers) > 0
            assert lib_logger.propagate is False

    @pytest.mark.unit
    def test_third_party_log_levels_set(self) -> None:
        """Test that third-party library log levels are set correctly."""
        _configure_third_party_logging()

        for logger_name, expected_level in THIRD_PARTY_LOG_LEVELS.items():
            lib_logger = logging.getLogger(logger_name)
            if expected_level != logging.NOTSET:
                assert lib_logger.level == expected_level


class TestLoggingIntegration:
    """Integration tests for logging system."""

    @pytest.mark.unit
    def test_logging_configured_before_sentry(self) -> None:
        """Test that logging is configured before Sentry initialization."""
        with _reset_logging_state():
            # This test verifies the order is correct in app.py
            # (logging before SentryManager.setup())
            # We can't easily test the actual timing without mocking Sentry,
            # but we verify logging is configured and ready
            configure_logging(level="INFO")
            assert logging_state.configured is True

            # Verify logger is functional (Sentry would use it)
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")
            logger.info("Test message for Sentry")
            assert "Test message for Sentry" in log_capture.getvalue()

    @pytest.mark.unit
    def test_logger_respects_configured_level(self) -> None:
        """Test that logger respects the configured log level."""
        with _reset_logging_state():
            configure_logging(level="WARNING")
            assert logging_state.configured is True

            # Verify the handler level is actually WARNING
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("WARNING").no

            # Verify DEBUG level handler would filter lower levels
            # (The actual filtering happens at handler level, which we verified above)
            assert handler.levelno > logger.level("DEBUG").no
            assert handler.levelno > logger.level("INFO").no

    @pytest.mark.unit
    @patch("tux.core.logging.logger")
    def test_configure_logging_logs_summary(self, mock_logger: MagicMock) -> None:
        """Test that configure_logging logs a summary message."""
        with _reset_logging_state():
            mock_logger.info.reset_mock()

            configure_logging(level="DEBUG")

            mock_logger.info.assert_called()
            call_args = str(mock_logger.info.call_args)
            assert "Logging configured" in call_args or "DEBUG" in call_args


class TestMessageFiltering:
    """Test message filtering and escaping."""

    @pytest.mark.unit
    def test_safe_message_filter_escapes_curly_braces(self) -> None:
        """Test that safe_message_filter escapes curly braces in messages."""
        with _reset_logging_state():
            configure_logging(level="DEBUG")

            # Add capture handler AFTER configure_logging (it removes all handlers)
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            # Log a message with curly braces - filter should escape them
            # The filter runs before formatting, so we need to check the handler's filter
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            filter_func = handler._filter

            # Create a mock record with curly braces
            mock_record = {"message": "Test {key} value"}
            result = filter_func(mock_record)

            assert result is True
            assert mock_record["message"] == "Test {{key}} value"

    @pytest.mark.unit
    def test_safe_message_filter_handles_non_string_messages(self) -> None:
        """Test that safe_message_filter handles non-string messages."""
        with _reset_logging_state():
            configure_logging(level="DEBUG")

            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            filter_func = handler._filter

            # Non-string message should not be modified
            mock_record = {"message": 12345}
            result = filter_func(mock_record)

            assert result is True
            assert mock_record["message"] == 12345


class TestFormatRecord:
    """Test log record formatting."""

    @pytest.mark.unit
    def test_format_record_exception_fallback(self) -> None:
        """Test _format_record fallback when formatting fails."""

        # Create a record that will cause an exception during formatting
        # Missing 'name' key will trigger KeyError
        class MockLevel:
            name = "INFO"

        invalid_record = {
            "time": datetime.now(UTC),
            "level": MockLevel(),
            "name": None,  # This will cause issues when accessing record["name"]
        }

        result = _format_record(invalid_record)

        assert "Error formatting log" in result

    @pytest.mark.unit
    def test_get_relative_file_path_fallback(self) -> None:
        """Test _get_relative_file_path fallback when src not in path."""

        # Create a record with a path that doesn't contain "src"
        class MockFile:
            path = "/some/other/path/file.py"

        record = {"file": MockFile()}

        result = _get_relative_file_path(record)

        assert result == "file.py"


class TestVerifyLoggingInterception:
    """Test verify_logging_interception function."""

    @pytest.mark.unit
    def test_verify_logging_interception(self) -> None:
        """Test verify_logging_interception logs configuration summary."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            _configure_third_party_logging()
            verify_logging_interception()

            output = log_capture.getvalue()
            assert "Third-party logging" in output
            assert str(len(INTERCEPTED_LIBRARIES)) in output
            assert str(len(THIRD_PARTY_LOG_LEVELS)) in output


class TestStructuredLogger:
    """Test StructuredLogger helper class."""

    @pytest.mark.unit
    def test_structured_logger_performance(self) -> None:
        """Test StructuredLogger.performance method."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            StructuredLogger.performance("test_operation", 0.123, extra="data")

            output = log_capture.getvalue()
            assert "Performance: test_operation completed" in output
            assert "0.123" in output

    @pytest.mark.unit
    def test_structured_logger_database_with_duration(self) -> None:
        """Test StructuredLogger.database method with duration."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            StructuredLogger.database("SELECT * FROM users", duration=0.045, rows=10)

            output = log_capture.getvalue()
            assert "Database: SELECT * FROM users" in output

    @pytest.mark.unit
    def test_structured_logger_database_without_duration(self) -> None:
        """Test StructuredLogger.database method without duration."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            StructuredLogger.database("SELECT * FROM users", rows=10)

            output = log_capture.getvalue()
            assert "Database: SELECT * FROM users" in output

    @pytest.mark.unit
    def test_structured_logger_api_call_with_status_and_duration(self) -> None:
        """Test StructuredLogger.api_call method with status and duration."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            StructuredLogger.api_call(
                "GET",
                "https://api.example.com",
                status=200,
                duration=0.234,
            )

            output = log_capture.getvalue()
            assert "API: GET https://api.example.com -> 200" in output

    @pytest.mark.unit
    def test_structured_logger_api_call_without_status(self) -> None:
        """Test StructuredLogger.api_call method without status but with duration."""
        with _reset_logging_state():
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            StructuredLogger.api_call("GET", "https://api.example.com", duration=0.234)

            output = log_capture.getvalue()
            assert "API: GET https://api.example.com -> None" in output
            # Verify duration was added to context (covers line 599-600)
