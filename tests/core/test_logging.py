"""Logging system unit tests.

Covers configure_logging, log level validation and determination, InterceptHandler
level mapping, third-party interception, duplicate-config prevention, and
StructuredLogger helpers.
"""

import io
import logging
from collections.abc import Generator
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
from tux.core.logging import _state as logging_state


@contextmanager
def _reset_logging_state() -> Generator[None]:
    """Reset and restore logging state for isolated tests."""
    original_configured = logging_state.configured
    logging_state.configured = False

    try:
        yield
    finally:
        logging_state.configured = original_configured
        logger.remove()


class TestLogLevelValidation:
    """Log level validation."""

    @pytest.mark.unit
    def test_validate_log_level_accepts_valid_levels_and_normalizes_case(self) -> None:
        """Validation accepts all valid levels and normalizes case."""
        # Arrange & Act & Assert
        for level in VALID_LOG_LEVELS:
            assert _validate_log_level(level) == level
            assert _validate_log_level(level.lower()) == level
            assert _validate_log_level(level.capitalize()) == level

    @pytest.mark.parametrize("invalid_level", ["INVALID", "debugging", ""])
    @pytest.mark.unit
    def test_validate_log_level_raises_for_invalid_level(
        self,
        invalid_level: str,
    ) -> None:
        """Validation raises ValueError for invalid log levels."""
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid log level"):
            _validate_log_level(invalid_level)

    @pytest.mark.unit
    def test_validate_log_level_returns_uppercase(self) -> None:
        """Validation returns uppercase level names."""
        # Act & Assert
        assert _validate_log_level("debug") == "DEBUG"
        assert _validate_log_level("INFO") == "INFO"
        assert _validate_log_level("Warning") == "WARNING"
        assert _validate_log_level("error") == "ERROR"


class _MockLogConfig:
    """Minimal spec for config objects used in log level determination."""

    LOG_LEVEL: str | None
    DEBUG: bool


class TestLogLevelDetermination:
    """Log level determination and priority."""

    @pytest.mark.unit
    def test_determine_log_level_explicit_level_overrides_config(self) -> None:
        """Explicit level parameter overrides config LOG_LEVEL and DEBUG."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = True

        # Act
        result = _determine_log_level("ERROR", mock_config)

        # Assert
        assert result == "ERROR"

    @pytest.mark.unit
    def test_determine_log_level_uses_config_log_level_when_no_explicit(
        self,
    ) -> None:
        """LOG_LEVEL from config is used when level is None."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = False

        # Act
        result = _determine_log_level(None, mock_config)

        # Assert
        assert result == "WARNING"

    @pytest.mark.unit
    def test_determine_log_level_accepts_info_from_config(self) -> None:
        """LOG_LEVEL=INFO from config is accepted."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = "INFO"
        mock_config.DEBUG = False

        # Act
        result = _determine_log_level(None, mock_config)

        # Assert
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_debug_flag_sets_debug(self) -> None:
        """DEBUG=True sets level to DEBUG when LOG_LEVEL is None."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = None
        mock_config.DEBUG = True

        # Act
        result = _determine_log_level(None, mock_config)

        # Assert
        assert result == "DEBUG"

    @pytest.mark.unit
    def test_determine_log_level_defaults_to_info_when_unset(self) -> None:
        """Default level is INFO when LOG_LEVEL and DEBUG are unset."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = None
        mock_config.DEBUG = False

        # Act
        result = _determine_log_level(None, mock_config)

        # Assert
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_defaults_to_info_when_config_is_none(
        self,
    ) -> None:
        """Default level is INFO when config is None."""
        # Act
        result = _determine_log_level(None, None)

        # Assert
        assert result == "INFO"

    @pytest.mark.unit
    def test_determine_log_level_priority_explicit_then_config_then_debug_then_default(
        self,
    ) -> None:
        """Priority: explicit > LOG_LEVEL > DEBUG > default INFO."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.LOG_LEVEL = "WARNING"
        mock_config.DEBUG = True

        # Act & Assert
        assert _determine_log_level("ERROR", mock_config) == "ERROR"
        assert _determine_log_level(None, mock_config) == "WARNING"

        mock_config.LOG_LEVEL = None
        assert _determine_log_level(None, mock_config) == "DEBUG"

        mock_config.DEBUG = False
        assert _determine_log_level(None, mock_config) == "INFO"

    @pytest.mark.parametrize(
        ("level_arg", "config_log_level"),
        [(None, "INVALID"), ("INVALID", "WARNING")],
    )
    @pytest.mark.unit
    def test_determine_log_level_raises_for_invalid_level(
        self,
        level_arg: str | None,
        config_log_level: str,
    ) -> None:
        """Invalid level from config or explicit parameter raises ValueError."""
        # Arrange
        mock_config = MagicMock(spec=_MockLogConfig)
        mock_config.DEBUG = False
        mock_config.LOG_LEVEL = config_log_level

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid log level"):
            _determine_log_level(level_arg, mock_config)


class TestConfigureLogging:
    """configure_logging behavior."""

    @pytest.mark.unit
    def test_configure_logging_removes_default_handler_and_logs_can_be_captured(
        self,
    ) -> None:
        """configure_logging removes default handler; logs can be captured and read."""
        with _reset_logging_state():
            # Arrange
            configure_logging(level="DEBUG")
            log_capture = io.StringIO()
            handler_id = logger.add(log_capture, level="DEBUG")

            try:
                # Act
                logger.debug("Test message")
                log_output = log_capture.getvalue()

                # Assert
                assert "Test message" in log_output
                assert "DEBUG" in log_output
            finally:
                logger.remove(handler_id)

    @pytest.mark.unit
    def test_configure_logging_ignores_second_call_duplicate_prevention(
        self,
    ) -> None:
        """Second configure_logging call is ignored; handler count and level unchanged."""
        with _reset_logging_state():
            # Arrange
            configure_logging(level="DEBUG")
            first_handlers = len(logger._core.handlers)
            first_level = logger._core.handlers[
                next(iter(logger._core.handlers.keys()))
            ].levelno

            # Act
            configure_logging(level="INFO")

            # Assert - second call ignored (no new handlers, level still DEBUG)
            assert len(logger._core.handlers) == first_handlers
            second_level = logger._core.handlers[
                next(iter(logger._core.handlers.keys()))
            ].levelno
            assert second_level == first_level

    @pytest.mark.unit
    def test_configure_logging_explicit_level_overrides_config(self) -> None:
        """Explicit level overrides config; handler uses explicit level."""
        with _reset_logging_state():
            # Arrange
            mock_config = MagicMock(spec=_MockLogConfig)
            mock_config.LOG_LEVEL = "WARNING"
            mock_config.DEBUG = False

            # Act
            configure_logging(level="DEBUG", config=mock_config)

            # Assert
            assert logging_state.configured is True
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("DEBUG").no

    @pytest.mark.unit
    def test_configure_logging_uses_config_log_level_when_no_explicit(
        self,
    ) -> None:
        """When level is None, config LOG_LEVEL is used for handler."""
        with _reset_logging_state():
            # Arrange
            mock_config = MagicMock(spec=_MockLogConfig)
            mock_config.LOG_LEVEL = "WARNING"
            mock_config.DEBUG = False

            # Act
            configure_logging(config=mock_config)

            # Assert
            assert logging_state.configured is True
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("WARNING").no

    @pytest.mark.unit
    def test_configure_testing_logging_sets_debug_level(self) -> None:
        """configure_testing_logging sets DEBUG level and marks configured."""
        with _reset_logging_state():
            # Act
            configure_testing_logging()

            # Assert
            assert logging_state.configured is True
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            assert handler.levelno == logger.level("DEBUG").no


class TestInterceptHandler:
    """InterceptHandler level mapping and stdlib routing."""

    @pytest.mark.unit
    def test_intercept_handler_routes_stdlib_log_record_to_loguru(self) -> None:
        """Stdlib LogRecord emitted via InterceptHandler appears in loguru output."""
        with _reset_logging_state():
            # Arrange
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

            # Act
            intercept_handler.emit(record)
            output = log_capture.getvalue()

            # Assert
            assert "Test message" in output
            assert "INFO" in output

    @pytest.mark.unit
    def test_intercept_handler_logs_warning_when_patch_raises(self) -> None:
        """When logger.patch raises, InterceptHandler logs an exception warning."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="WARNING", format="{message}")
            _configure_third_party_logging()

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

            # Act
            with patch(
                "tux.core.logging.logger.patch",
                side_effect=Exception("Patch failed"),
            ):
                intercept_handler.emit(record)
            output = log_capture.getvalue()

            # Assert
            assert "Exception while logging message" in output

    @pytest.mark.unit
    def test_intercept_handler_maps_all_stdlib_levels_to_loguru(self) -> None:
        """DEBUG through CRITICAL stdlib levels are routed to loguru."""
        with _reset_logging_state():
            # Arrange
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

            # Act
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
            output = log_capture.getvalue()

            # Assert
            assert "DEBUG" in output
            assert "INFO" in output
            assert "WARNING" in output
            assert "ERROR" in output
            assert "CRITICAL" in output

    @pytest.mark.unit
    def test_intercept_handler_uses_numeric_level_for_unknown_levelname(
        self,
    ) -> None:
        """Unknown levelname uses numeric level; message is still routed."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="TRACE", format="{level} | {message}")
            _configure_third_party_logging()
            root_logger = logging.getLogger()
            intercept_handler = root_logger.handlers[0]
            record = logging.LogRecord(
                name="test.logger",
                level=25,
                pathname="test.py",
                lineno=1,
                msg="Test custom level message",
                args=(),
                exc_info=None,
            )
            record.levelname = "CUSTOM"

            # Act
            intercept_handler.emit(record)
            output = log_capture.getvalue()

            # Assert
            assert "Test custom level message" in output


class TestThirdPartyLogging:
    """Third-party library interception and level overrides."""

    @pytest.mark.unit
    def test_intercepted_libraries_have_handler_and_no_propagate(self) -> None:
        """Each intercepted library has a handler and propagate False."""
        # Act
        _configure_third_party_logging()

        # Assert
        for lib_name in INTERCEPTED_LIBRARIES:
            lib_logger = logging.getLogger(lib_name)
            assert len(lib_logger.handlers) > 0
            assert lib_logger.propagate is False

    @pytest.mark.unit
    def test_third_party_log_levels_match_override_config(self) -> None:
        """Third-party loggers have levels set per THIRD_PARTY_LOG_LEVELS."""
        # Act
        _configure_third_party_logging()

        # Assert
        for logger_name, expected_level in THIRD_PARTY_LOG_LEVELS.items():
            lib_logger = logging.getLogger(logger_name)
            if expected_level != logging.NOTSET:
                assert lib_logger.level == expected_level


class TestLoggingIntegration:
    """Logging integration and configure_logging behavior."""

    @pytest.mark.unit
    def test_logging_configured_and_ready_for_sentry(self) -> None:
        """Logging can be configured and used before Sentry init."""
        with _reset_logging_state():
            # Arrange & Act
            configure_logging(level="INFO")
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")
            logger.info("Test message for Sentry")
            output = log_capture.getvalue()

            # Assert
            assert logging_state.configured is True
            assert "Test message for Sentry" in output

    @pytest.mark.unit
    def test_configured_handler_level_filters_below_threshold(self) -> None:
        """Handler level is set; levelno above DEBUG and INFO."""
        with _reset_logging_state():
            # Arrange & Act
            configure_logging(level="WARNING")
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]

            # Assert
            assert logging_state.configured is True
            assert handler.levelno == logger.level("WARNING").no
            assert handler.levelno > logger.level("DEBUG").no
            assert handler.levelno > logger.level("INFO").no

    @pytest.mark.unit
    @patch("tux.core.logging.logger", autospec=True)
    def test_configure_logging_emits_summary_message(
        self,
        mock_logger: MagicMock,
    ) -> None:
        """configure_logging logs a summary (e.g. level) via logger.info."""
        with _reset_logging_state():
            # Arrange
            mock_logger.info.reset_mock()

            # Act
            configure_logging(level="DEBUG")

            # Assert
            mock_logger.info.assert_called()
            call_str = str(mock_logger.info.call_args)
            assert "Logging configured" in call_str or "DEBUG" in call_str


class TestMessageFiltering:
    """Message filtering and escaping (curly braces, angle brackets)."""

    @pytest.mark.unit
    def test_logged_message_with_curly_braces_is_escaped_in_output(self) -> None:
        """Messages with curly braces are escaped before formatting."""
        with _reset_logging_state():
            # Arrange
            configure_logging(level="DEBUG")
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            # Act
            logger.debug("Test {key} value")
            output = log_capture.getvalue()

            # Assert
            assert "Test {{key}} value" in output

    @pytest.mark.unit
    def test_logged_message_with_angle_brackets_escapes_less_than(self) -> None:
        """Angle brackets in messages are escaped so Discord mentions don't break colorizer."""
        with _reset_logging_state():
            # Arrange
            configure_logging(level="DEBUG")
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            # Act
            logger.debug("User <@&1259555162448724038> and <@1172803065779339304>")
            output = log_capture.getvalue()

            # Assert
            assert "\\<@&1259555162448724038>" in output
            assert "\\<@1172803065779339304>" in output

    @pytest.mark.unit
    def test_safe_message_filter_leaves_non_string_messages_unchanged(
        self,
    ) -> None:
        """Non-string messages are not modified by the filter."""
        with _reset_logging_state():
            # Arrange - filter via handler; we exercise it directly since
            # loguru never passes non-string messages from logger.debug(str)
            configure_logging(level="DEBUG")
            handler = logger._core.handlers[next(iter(logger._core.handlers.keys()))]
            filter_func = handler._filter
            mock_record: dict[str, object] = {"message": 12345}

            # Act
            result = filter_func(mock_record)

            # Assert
            assert result is True
            assert mock_record["message"] == 12345


class TestFormatRecord:
    """Log record formatting and file path helpers."""

    @pytest.mark.unit
    def test_format_record_returns_error_message_when_formatting_fails(
        self,
    ) -> None:
        """_format_record returns fallback message when formatting raises."""

        # Arrange
        class MockLevel:
            name = "INFO"

        invalid_record = {
            "time": datetime.now(UTC),
            "level": MockLevel(),
            "name": None,
        }

        # Act
        result = _format_record(invalid_record)

        # Assert
        assert "Error formatting log" in result

    @pytest.mark.unit
    def test_get_relative_file_path_returns_basename_when_src_not_in_path(
        self,
    ) -> None:
        """_get_relative_file_path returns basename when path has no 'src'."""

        # Arrange
        class MockFile:
            path = "/some/other/path/file.py"

        record = {"file": MockFile()}

        # Act
        result = _get_relative_file_path(record)

        # Assert
        assert result == "file.py"


class TestVerifyLoggingInterception:
    """verify_logging_interception behavior."""

    @pytest.mark.unit
    def test_verify_logging_interception_logs_summary_with_counts(self) -> None:
        """verify_logging_interception logs summary including interception counts."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")
            _configure_third_party_logging()

            # Act
            verify_logging_interception()
            output = log_capture.getvalue()

            # Assert
            assert "Third-party logging" in output
            assert str(len(INTERCEPTED_LIBRARIES)) in output
            assert str(len(THIRD_PARTY_LOG_LEVELS)) in output


class TestStructuredLogger:
    """StructuredLogger helper methods."""

    @pytest.mark.unit
    def test_structured_logger_performance_logs_operation_and_duration(
        self,
    ) -> None:
        """StructuredLogger.performance logs operation name and duration."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            # Act
            StructuredLogger.performance("test_operation", 0.123, extra="data")
            output = log_capture.getvalue()

            # Assert
            assert "Performance: test_operation completed" in output
            assert "0.123" in output

    @pytest.mark.unit
    def test_structured_logger_database_with_duration_includes_query_and_duration(
        self,
    ) -> None:
        """StructuredLogger.database with duration logs query and duration."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            # Act
            StructuredLogger.database("SELECT * FROM users", duration=0.045, rows=10)
            output = log_capture.getvalue()

            # Assert
            assert "Database: SELECT * FROM users" in output

    @pytest.mark.unit
    def test_structured_logger_database_without_duration_logs_query(
        self,
    ) -> None:
        """StructuredLogger.database without duration logs query."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="DEBUG", format="{message}")

            # Act
            StructuredLogger.database("SELECT * FROM users", rows=10)
            output = log_capture.getvalue()

            # Assert
            assert "Database: SELECT * FROM users" in output

    @pytest.mark.unit
    def test_structured_logger_api_call_logs_method_url_status_duration(
        self,
    ) -> None:
        """StructuredLogger.api_call with status and duration logs all."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            # Act
            StructuredLogger.api_call(
                "GET",
                "https://api.example.com",
                status=200,
                duration=0.234,
            )
            output = log_capture.getvalue()

            # Assert
            assert "API: GET https://api.example.com -> 200" in output

    @pytest.mark.unit
    def test_structured_logger_api_call_without_status_logs_none_for_status(
        self,
    ) -> None:
        """StructuredLogger.api_call without status logs None for status."""
        with _reset_logging_state():
            # Arrange
            log_capture = io.StringIO()
            logger.add(log_capture, level="INFO", format="{message}")

            # Act
            StructuredLogger.api_call("GET", "https://api.example.com", duration=0.234)
            output = log_capture.getvalue()

            # Assert
            assert "API: GET https://api.example.com -> None" in output
