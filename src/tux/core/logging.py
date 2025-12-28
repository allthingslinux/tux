"""Centralized loguru configuration for Tux Discord bot.

This module provides clean, standardized logging setup following loguru best
practices: single global logger configuration, environment-based configuration,
structured logging helpers, third-party library log interception, and IDE-clickable
file paths. Log level is determined in this order (highest to lowest): explicit
level parameter (for testing), CONFIG.LOG_LEVEL from .env file, CONFIG.DEBUG=1
sets DEBUG level, or default "INFO".
"""

from __future__ import annotations

import contextlib
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

if TYPE_CHECKING:
    from tux.shared.config.settings import Config

__all__ = [
    "configure_logging",
    "configure_testing_logging",
    "StructuredLogger",
    "verify_logging_interception",
    "VALID_LOG_LEVELS",
]


# Libraries whose logs should be intercepted and routed through loguru
INTERCEPTED_LIBRARIES = [
    "discord",
    "discord.client",
    "discord.gateway",
    "discord.http",
    "discord.app_commands",  # Slash commands and app command tree
    "discord.ui",  # UI components (buttons, modals, views)
    "jishaku",
    "aiohttp",
    "httpx",
    "urllib3",
    "h2",  # HTTP/2 library (used by httpx)
    "asyncio",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.pool.impl",  # Pool implementation details (very verbose)
    "sqlalchemy.orm",
    "sqlalchemy.dialects",
    "alembic",
    "asyncpg",
    "psycopg",
    "sentry_sdk",
    "githubkit",
    "influxdb_client",
    "watchdog",
    "pydantic",  # Data validation (validation errors)
    "pydantic_settings",  # Settings management (config loading)
    "typer",  # CLI framework (CLI operations)
    "reactionmenu",  # Discord reaction menu library
]

# These override the global level to either reduce spam or set appropriate levels
THIRD_PARTY_LOG_LEVELS = {
    # Discord.py - Suppress verbose DEBUG spam (websocket events, API payloads)
    # Gateway and HTTP are INFO to show connection events but suppress DEBUG spam
    "discord.gateway": logging.INFO,
    "discord.client": logging.INFO,
    "discord.http": logging.INFO,
    # App commands and UI components - INFO for important events
    "discord.app_commands": logging.INFO,
    "discord.ui": logging.INFO,
    "jishaku": logging.INFO,
    # File watching - Suppress file I/O spam
    "watchdog": logging.WARNING,
    "watchdog.observers": logging.WARNING,
    # HTTP clients - Suppress request/response details (very verbose)
    "urllib3": logging.WARNING,
    "httpx": logging.WARNING,
    "aiohttp": logging.WARNING,
    # Database - Fine-grained control per subsystem
    # Engine: WARNING to suppress SQL query spam (use DEBUG when needed for query debugging)
    "sqlalchemy.engine": logging.WARNING,
    # Pool: WARNING to suppress very verbose connection pool operations
    # Pool operations (checkout, return, reset, pre-ping) are step-by-step execution tracking
    # that are TRACE-level detail. These logs show every connection lifecycle event:
    # - checkout: Getting a connection from the pool
    # - pre-ping: Validating connection is alive before use
    # - __connect: Creating new connection when pool is empty
    # - return/finalize: Returning connection back to pool after use
    # - reset: Cleaning up connection (rollback) before returning to pool
    # These are too verbose for normal DEBUG logging. Set to DEBUG only when debugging
    # connection pool issues (leaks, timeouts, connection problems).
    "sqlalchemy.pool": logging.WARNING,
    # Pool implementation details - even more verbose than sqlalchemy.pool
    "sqlalchemy.pool.impl": logging.WARNING,
    # ORM: WARNING to suppress very noisy ORM internals
    "sqlalchemy.orm": logging.WARNING,
    # Dialects: WARNING to suppress dialect-specific details
    "sqlalchemy.dialects": logging.WARNING,
    # Migration tooling - INFO for migration progress
    "alembic": logging.INFO,
    # Database drivers - INFO for connection events
    "asyncpg": logging.INFO,
    "psycopg": logging.INFO,
    # HTTP/2 - Suppress HTTP/2 protocol details (very verbose)
    "h2": logging.WARNING,
    # Data validation - INFO for validation errors (useful for debugging)
    "pydantic": logging.INFO,
    # Settings management - INFO for config loading events
    "pydantic_settings": logging.INFO,
    # CLI framework - INFO for CLI operations
    "typer": logging.INFO,
    # Discord reaction menu - INFO for menu operations
    "reactionmenu": logging.INFO,
    # Use global level (no override needed, just for explicitness)
    "asyncio": logging.NOTSET,
    "discord": logging.NOTSET,  # Parent logger, children have specific levels
    "sqlalchemy": logging.NOTSET,  # Parent logger, children have specific levels
    "githubkit": logging.NOTSET,
    "influxdb_client": logging.NOTSET,
    "sentry_sdk": logging.NOTSET,
}

# Custom colors for each log level (more vibrant and distinguished)
LEVEL_COLORS = {
    "TRACE": "<dim><white>",  # Dim white - very low priority
    "DEBUG": "<dim><cyan>",  # Dim cyan - debug info (grayish)
    "INFO": "<bold><white>",  # Bold white - standard messages
    "SUCCESS": "<bold><green>",  # Bold green - achievements
    "WARNING": "<bold><yellow>",  # Bold yellow - needs attention
    "ERROR": "<bold><red>",  # Bold red - problems
    "CRITICAL": "<bold><magenta>",  # Bold magenta - severe issues
}

# Maximum message length before truncation (prevents recursion errors with huge JSON)
MAX_MESSAGE_LENGTH = 500

# Valid loguru log levels
VALID_LOG_LEVELS = {"TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}


class _LoggingState:
    """Prevents duplicate logging configuration."""

    configured = False


_state = _LoggingState()


def configure_testing_logging() -> None:
    """
    Configure logging specifically for testing environment.

    Sets up logging with DEBUG level and testing-appropriate configuration.
    Call this once at test startup.
    """
    configure_logging(level="DEBUG")


def configure_logging(
    environment: str | None = None,  # Deprecated, kept for compatibility
    level: str | None = None,
    config: Config | None = None,
) -> None:
    """
    Configure the global loguru logger for the Tux application.

    Main entry point for logging configuration. Call once at startup. Log level
    is determined by: explicit level parameter (highest priority), config.LOG_LEVEL,
    config.DEBUG setting, or default "INFO".

    Parameters
    ----------
    environment : str | None, optional
        Deprecated parameter, kept for backward compatibility.
    level : str | None, optional
        Explicit log level override (for testing). Highest priority.
    config : Config | None, optional
        Config instance with LOG_LEVEL and DEBUG from .env file.

    Examples
    --------
    >>> from tux.shared.config import CONFIG
    >>> configure_logging(config=CONFIG)  # Normal usage
    >>> configure_logging(level="DEBUG")  # Override for testing
    """
    # Prevent duplicate configuration
    if _state.configured:
        return
    _state.configured = True

    # Remove loguru's default handler
    logger.remove()

    # Configure custom colors for better visual hierarchy
    _configure_level_colors()

    # Determine log level from configuration
    log_level = _determine_log_level(level, config)

    # Add console handler with custom formatting
    _add_console_handler(log_level)

    # Intercept third-party library logs and route to loguru
    _configure_third_party_logging()

    # Log configuration summary
    logger.info(f"Logging configured at {log_level} level")


def _configure_level_colors() -> None:
    """Configure custom colors for each log level."""
    for level_name, color in LEVEL_COLORS.items():
        logger.level(level_name, color=color)


def _validate_log_level(level: str) -> str:
    """
    Validate and normalize log level name.

    Parameters
    ----------
    level : str
        Log level name to validate.

    Returns
    -------
    str
        Normalized (uppercase) log level name.

    Raises
    ------
    ValueError
        If the log level is not a valid loguru level.
    """
    level_upper = level.upper()
    if level_upper not in VALID_LOG_LEVELS:
        valid_levels = ", ".join(sorted(VALID_LOG_LEVELS))
        error_msg = f"Invalid log level '{level}'. Must be one of: {valid_levels}"
        raise ValueError(error_msg)
    return level_upper


def _determine_log_level(level: str | None, config: Config | None) -> str:
    # sourcery skip: assign-if-exp, reintroduce-else
    """
    Determine the log level from multiple sources.

    Priority (highest to lowest): explicit level parameter, config.LOG_LEVEL
    (from .env), config.DEBUG (sets DEBUG), or default "INFO".

    Parameters
    ----------
    level : str | None
        Explicit level override.
    config : Config | None
        Config instance from .env.

    Returns
    -------
    str
        The determined log level (normalized to uppercase and validated).
    """
    # Explicit level parameter (highest priority - for testing)
    if level:
        return _validate_log_level(level)

    # Config LOG_LEVEL (from .env file)
    if config and config.LOG_LEVEL:
        return _validate_log_level(config.LOG_LEVEL)

    # DEBUG flag (sets DEBUG level)
    if config and config.DEBUG:
        return "DEBUG"

    # Default
    return "INFO"


def _add_console_handler(log_level: str) -> None:
    """
    Add console handler with custom formatting.

    Uses a dynamic stderr sink for robustness against stream wrapping (e.g., by
    pytest, IDEs, cloud platforms).

    Parameters
    ----------
    log_level : str
        The minimum log level to display.
    """

    def stderr_sink(message: str) -> None:
        """Dynamically retrieve sys.stderr for robustness."""
        sys.stderr.write(message)

    def safe_message_filter(record: Any) -> bool:
        """
        Filter that escapes curly braces in log messages to prevent format errors.

        This prevents dictionaries and strings with braces from being interpreted
        as format placeholders by Loguru, fixing issues like KeyError with dict keys.

        Parameters
        ----------
        record : Any
            The loguru Record object (dict-like) to process.

        Returns
        -------
        bool
            Always True to allow the log message through.
        """
        # Escape curly braces in the message to prevent format string interpretation
        if isinstance(record["message"], str):
            record["message"] = record["message"].replace("{", "{{").replace("}", "}}")
        return True

    logger.add(
        stderr_sink,
        format=_format_record,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,  # Shows variable values in tracebacks
        enqueue=False,  # Synchronous for console
        catch=True,  # Catch errors in logging itself
        filter=safe_message_filter,  # Automatically escape braces in all messages
    )


def _format_record(record: Any) -> str:
    """
    Format log record with IDE-clickable file paths and proper escaping.

    For tux.* modules: shows clickable path (src/tux/core/app.py:167). For
    third-party: shows module:function (urllib3.connectionpool:_make_request:544).

    Parameters
    ----------
    record : Any
        The loguru Record object.

    Returns
    -------
    str
        Formatted log message with escaped special characters.
    """
    try:
        module_name = record["name"]

        # Determine location format based on source
        if module_name.startswith("tux."):
            # Our code - show clickable file path
            location = _get_relative_file_path(record)
        else:
            # Third-party - show module:function
            function = record.get("function", "")
            location = f"{module_name}:{function}" if function else module_name

        # Escape special characters to prevent format string interpretation
        location = _escape_format_chars(location)

        # Build formatted output
        return (
            f"<green>{record['time']:HH:mm:ss.SSS}</green> | "
            f"<level>{record['level'].name: <8}</level> | "
            f"<cyan>{location}</cyan>:<cyan>{record['line']}</cyan> | "
            f"<level>{record['message']}</level>\n"
        )
    except Exception:
        # Fallback if formatting fails
        return f"{record['time']} | {record['level'].name} | {record['name']} | Error formatting log\n"


def _get_relative_file_path(record: Any) -> str:
    """
    Get file path relative to project root (from src/ directory).

    Parameters
    ----------
    record : Any
        The loguru Record object.

    Returns
    -------
    str
        Relative file path from src/ (e.g., "src/tux/core/app.py").
    """
    file_path = Path(record["file"].path)
    parts = file_path.parts

    # Try to build relative path from src/ directory
    if "src" in parts:
        with contextlib.suppress(ValueError, IndexError):
            src_index = parts.index("src")
            return str(Path(*parts[src_index:]))

    # Fallback to just filename
    return file_path.name


def _escape_format_chars(text: str | Any) -> str:
    """
    Escape special characters that could be interpreted as format placeholders.

    Escapes:
    - Curly braces {{ }} to prevent format string errors
    - Angle brackets <> to prevent color tag errors

    Parameters
    ----------
    text : str | Any
        Text to escape.

    Returns
    -------
    str
        Escaped text safe for loguru formatting.
    """
    text = str(text)
    # Escape curly braces (format strings): {application_id} -> {{application_id}}
    text = text.replace("{", "{{").replace("}", "}}")
    # Escape angle brackets (color tags): <locals> -> \<locals\>
    return text.replace("<", r"\<").replace(">", r"\>")


def _configure_third_party_logging() -> None:
    """
    Configure logging interception for third-party libraries.

    Sets up an InterceptHandler that routes standard library logging calls to
    loguru, maintaining proper source attribution for all logs. Creates
    InterceptHandler to bridge logging -> loguru, replaces root logging handler
    globally, configures specific library loggers with InterceptHandler, and sets
    appropriate minimum levels for third-party libraries.
    """

    class InterceptHandler(logging.Handler):
        """
        Bridge handler that routes standard logging to loguru.

        Preserves original source information (module, function, line) from the
        logging.LogRecord for accurate log attribution.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """Emit a log record to loguru.

            Parameters
            ----------
            record : logging.LogRecord
                The standard library log record to route to loguru.
            """
            # Map standard library level names to loguru level names
            level_mapping = {
                "DEBUG": "DEBUG",
                "INFO": "INFO",
                "WARNING": "WARNING",
                "ERROR": "ERROR",
                "CRITICAL": "CRITICAL",
            }

            # Try mapping first, then loguru lookup, then numeric fallback
            level_name = level_mapping.get(record.levelname, record.levelname)
            try:
                level = logger.level(level_name).name
            except ValueError:
                # Fallback to numeric level (loguru will handle it)
                level = str(record.levelno)

            # Route to loguru with original source information
            try:
                # Get message and escape curly braces to prevent format string errors
                message = record.getMessage()
                # Escape curly braces in message (e.g., JSON content) to prevent
                # loguru from interpreting them as format placeholders
                escaped_message = message.replace("{", "{{").replace("}", "}}")

                logger.patch(
                    lambda r: r.update(
                        name=record.name,  # e.g., "discord.gateway"
                        function=record.funcName,  # e.g., "on_ready"
                        line=record.lineno,  # Line number
                    ),
                ).opt(exception=record.exc_info).log(level, escaped_message)
            except Exception as e:
                # Fallback if patching fails
                safe_msg = getattr(record, "msg", None) or str(record)
                logger.opt(exception=record.exc_info).warning(
                    "Exception while logging message from {}: {} - Original: {!r}",
                    record.name,
                    e,
                    safe_msg,
                )

    # Replace root logging handler to intercept all logs
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Configure specific third-party library loggers
    for logger_name in INTERCEPTED_LIBRARIES:
        lib_logger = logging.getLogger(logger_name)
        lib_logger.handlers = [InterceptHandler()]
        lib_logger.propagate = False

    # Set minimum levels for third-party libraries
    for logger_name, level in THIRD_PARTY_LOG_LEVELS.items():
        logging.getLogger(logger_name).setLevel(level)


def verify_logging_interception() -> None:
    """
    Verify third-party library logging configuration (debug utility).

    Logs the configuration of all known third-party loggers, showing which
    handlers are attached and their current levels. Automatically called when
    DEBUG level is active.
    """
    # Group libraries by their configured level
    level_groups: dict[str, list[str]] = {}

    for lib_name in INTERCEPTED_LIBRARIES:
        lib_logger = logging.getLogger(lib_name)
        level_name = logging.getLevelName(lib_logger.level)

        if level_name not in level_groups:
            level_groups[level_name] = []
        level_groups[level_name].append(lib_name)

    # Log summary by level
    logger.debug(
        f"Third-party logging: {len(INTERCEPTED_LIBRARIES)} libraries intercepted, "
        f"{len(THIRD_PARTY_LOG_LEVELS)} with custom levels",
    )

    for level_name in sorted(level_groups.keys()):
        libs = ", ".join(sorted(level_groups[level_name]))
        logger.debug(f"  {level_name:8} → {libs}")


class StructuredLogger:
    """
    Helper class for structured logging with consistent context.

    Provides static methods for logging performance metrics, database operations,
    and API calls with structured context data for better log analysis.
    """

    @staticmethod
    def performance(operation: str, duration: float, **context: Any) -> None:
        """
        Log performance metrics with structured context.

        Parameters
        ----------
        operation : str
            Name of the operation being measured.
        duration : float
            Duration of the operation in seconds.
        **context : Any
            Additional context to bind to the log entry.

        Examples
        --------
        >>> StructuredLogger.performance(
        ...     "database_query", 0.123, query="SELECT * FROM users"
        ... )
        """
        logger.bind(
            operation=operation,
            duration_seconds=duration,
            **context,
        ).info(f"Performance: {operation} completed in {duration:.3f}s")

    @staticmethod
    def database(query: str, duration: float | None = None, **context: Any) -> None:
        """
        Log database operations with structured context.

        Parameters
        ----------
        query : str
            The SQL query being executed.
        duration : float | None, optional
            Query execution duration in seconds.
        **context : Any
            Additional context like table names, row counts, etc.

        Examples
        --------
        >>> StructuredLogger.database(
        ...     "INSERT INTO users", duration=0.045, rows_affected=1
        ... )
        """
        log_context = {"query": query, **context}
        if duration is not None:
            log_context["duration_seconds"] = duration

        logger.bind(**log_context).debug(f"Database: {query}")

    @staticmethod
    def api_call(
        method: str,
        url: str,
        status: int | None = None,
        duration: float | None = None,
        **context: Any,
    ) -> None:
        """
        Log external API calls with structured context.

        Parameters
        ----------
        method : str
            HTTP method (GET, POST, etc.).
        url : str
            The API endpoint URL.
        status : int | None, optional
            HTTP response status code.
        duration : float | None, optional
            Request duration in seconds.
        **context : Any
            Additional context like response size, error details, etc.

        Examples
        --------
        >>> StructuredLogger.api_call(
        ...     "GET", "https://api.github.com/user", status=200, duration=0.234
        ... )
        """
        log_context = {"method": method, "url": url, **context}
        if status is not None:
            log_context["status"] = status
        if duration is not None:
            log_context["duration_seconds"] = duration

        logger.bind(**log_context).info(f"API: {method} {url} -> {status}")
