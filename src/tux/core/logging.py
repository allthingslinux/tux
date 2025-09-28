"""
Centralized Loguru Configuration for Tux Discord Bot.

This module provides a clean, standardized logging setup following loguru best practices:
- Single global logger configuration
- Environment-based configuration
- Structured logging helpers
- Performance optimizations
- Testing compatibility
"""

import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger


class _LoggingState:
    """Simple state holder for logging configuration."""

    configured = False


_state = _LoggingState()


def configure_logging(
    environment: str | None = None,  # Keep for backward compatibility but ignore
    level: str | None = None,
    enable_file_logging: bool | None = None,
) -> None:
    """
    Configure the global loguru logger for the Tux application.

    This function can be called multiple times but will only configure logging once.
    Subsequent calls will be ignored to prevent duplicate configuration.

    Args:
        environment: Deprecated parameter, kept for backward compatibility.
        level: Override log level. If None, uses LOG_LEVEL env var (defaults to INFO).
        enable_file_logging: Override file logging. If None, uses default behavior.
    """
    # Prevent multiple configurations using state object
    if _state.configured:
        return

    _state.configured = True

    # Remove default handler first (loguru best practice)
    logger.remove()

    # Application configuration - simplified to single source
    log_level = level or os.getenv("LOG_LEVEL", "INFO")
    console_format = _get_console_format()
    file_logging = enable_file_logging if enable_file_logging is not None else _should_enable_file_logging()

    # Console logging configuration
    logger.add(
        sys.stderr,
        format=console_format,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
        enqueue=False,  # Keep synchronous for console output
        catch=True,
    )

    # File logging configuration (if enabled)
    if file_logging:
        _configure_file_logging(log_level)

    # Configure third-party library logging
    _configure_third_party_logging()

    # Log configuration summary
    logger.info(f"Logging configured at {log_level} level")


def _get_console_format() -> str:
    """Get console log format."""
    return "<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"


def _should_enable_file_logging() -> bool:
    """Determine if file logging should be enabled."""
    return os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"


def _configure_file_logging(log_level: str) -> None:
    """Configure file logging with rotation and retention."""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Main log file with rotation
    logger.add(
        logs_dir / "tux_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.name}:{thread.name} | {name}:{function}:{line} | {message}",
        level=log_level,
        rotation="00:00",  # Rotate daily at midnight
        retention="30 days",  # Keep logs for 30 days
        compression="gz",  # Compress old logs
        serialize=False,  # Human-readable format
        enqueue=True,  # Thread-safe for multiprocessing
        backtrace=True,
        diagnose=True,
        catch=True,
    )

    # Error-only log file
    logger.add(
        logs_dir / "tux_errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {process.name}:{thread.name} | {name}:{function}:{line} | {message}\n{exception}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",  # Keep error logs longer
        compression="gz",
        serialize=False,
        enqueue=True,
        backtrace=True,
        diagnose=True,  # Always diagnose errors
        catch=True,
    )


def _configure_third_party_logging() -> None:
    """Configure logging for third-party libraries."""

    # Intercept standard logging and redirect to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = inspect.currentframe(), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Replace standard logging handlers
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Configure specific third-party loggers
    third_party_loggers = [
        "discord",
        "discord.client",
        "discord.gateway",
        "discord.http",
        "aiohttp",
        "asyncio",
        "sqlalchemy",
        "alembic",
    ]

    for logger_name in third_party_loggers:
        logging.getLogger(logger_name).handlers = [InterceptHandler()]
        logging.getLogger(logger_name).propagate = False


# Structured logging helpers
class StructuredLogger:
    """Helper class for structured logging with consistent context."""

    @staticmethod
    def performance(operation: str, duration: float, **context: Any) -> None:
        """Log performance metrics with structured context."""
        logger.bind(
            operation_type="performance",
            operation=operation,
            duration_ms=round(duration * 1000, 2),
            **context,
        ).info(f"⏱️ {operation} completed in {duration:.3f}s")

    @staticmethod
    def database(operation: str, table: str, **context: Any) -> None:
        """Log database operations with structured context."""
        logger.bind(operation_type="database", db_operation=operation, table=table, **context).debug(
            f"🗄️ {operation} on {table}",
        )

    @staticmethod
    def api_request(method: str, url: str, status_code: int | None = None, **context: Any) -> None:
        """Log API requests with structured context."""
        logger.bind(operation_type="api_request", http_method=method, url=url, status_code=status_code, **context).info(
            f"🌐 {method} {url}" + (f" -> {status_code}" if status_code else ""),
        )

    @staticmethod
    def user_action(action: str, user_id: int, guild_id: int | None = None, **context: Any) -> None:
        """Log user actions with structured context."""
        logger.bind(operation_type="user_action", action=action, user_id=user_id, guild_id=guild_id, **context).info(
            f"👤 {action} by user {user_id}" + (f" in guild {guild_id}" if guild_id else ""),
        )

    @staticmethod
    def bot_event(event: str, **context: Any) -> None:
        """Log bot events with structured context."""
        logger.bind(operation_type="bot_event", event=event, **context).info(f"🤖 {event}")

    @staticmethod
    def error_with_context(error: Exception, context_msg: str, **context: Any) -> None:
        """Log errors with structured context and full exception details."""
        logger.bind(operation_type="error", error_type=error.__class__.__name__, context=context_msg, **context).opt(
            exception=True,
        ).error(f"❌ {context_msg}: {error}")


# Convenience aliases for structured logging
log_perf = StructuredLogger.performance
log_db = StructuredLogger.database
log_api = StructuredLogger.api_request
log_user = StructuredLogger.user_action
log_event = StructuredLogger.bot_event
log_error = StructuredLogger.error_with_context


# Testing support
def configure_testing_logging() -> None:
    """Configure logging for testing environment."""
    # Use unified function - same as development but may suppress noisy loggers via env vars
    configure_logging()


# Library usage pattern (for when Tux is used as a library)
def disable_tux_logging() -> None:
    """Disable Tux logging when used as a library."""
    logger.disable("tux")


def enable_tux_logging() -> None:
    """Re-enable Tux logging when used as a library."""
    logger.enable("tux")
