"""
Centralized Loguru Configuration for Tux Discord Bot.

This module provides clean, standardized logging setup following loguru best practices:
- Single global logger configuration
- Environment-based configuration
- Structured logging helpers
- Third-party library log interception
- IDE-clickable file paths

Configuration Priority
---------------------
Log level is determined in this order (highest to lowest):
1. Explicit `level` parameter (for testing)
2. `CONFIG.LOG_LEVEL` from .env file
3. `CONFIG.DEBUG=1` sets DEBUG level
4. Default "INFO"

Usage
-----
Call once at application startup:

    from tux.shared.config import CONFIG
    from tux.core.logging import configure_logging

    configure_logging(config=CONFIG)

For debugging specific issues, override the level:

    configure_logging(level="DEBUG")
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


# =============================================================================
# CONFIGURATION CONSTANTS
# =============================================================================

# Libraries whose logs should be intercepted and routed through loguru
INTERCEPTED_LIBRARIES = [
    "discord",
    "discord.client",
    "discord.gateway",
    "discord.http",
    "jishaku",
    "aiohttp",
    "httpx",
    "urllib3",
    "asyncio",
    "sqlalchemy",
    "sqlalchemy.engine",
    "sqlalchemy.pool",
    "sqlalchemy.orm",
    "sqlalchemy.dialects",
    "alembic",
    "asyncpg",
    "psycopg",
    "aiosqlite",
    "sentry_sdk",
    "redis",
    "docker",
    "githubkit",
    "influxdb_client",
    "watchdog",
]

# These override the global level to either reduce spam or set appropriate levels
THIRD_PARTY_LOG_LEVELS = {
    # Discord.py - Suppress verbose DEBUG spam (websocket events, API payloads)
    "discord.gateway": logging.INFO,
    "discord.client": logging.INFO,
    "discord.http": logging.INFO,
    "jishaku": logging.INFO,
    # File watching - Suppress file I/O spam
    "watchdog": logging.WARNING,
    "watchdog.observers": logging.WARNING,
    # HTTP clients - Suppress request/response details
    "urllib3": logging.WARNING,
    "httpx": logging.WARNING,
    "aiohttp": logging.WARNING,
    # Infrastructure - Rarely needed
    "redis": logging.WARNING,
    "docker": logging.WARNING,
    # Database - Fine-grained control per subsystem
    "sqlalchemy.engine": logging.WARNING,  # SQL queries and parameters (not result sets)
    "sqlalchemy.pool": logging.DEBUG,  # Connection pool events (not checkin/checkout spam)
    "sqlalchemy.orm": logging.WARNING,  # ORM internals (very noisy)
    "sqlalchemy.dialects": logging.WARNING,  # Dialect-specific details
    "alembic": logging.INFO,
    "asyncpg": logging.INFO,
    "psycopg": logging.INFO,
    "aiosqlite": logging.INFO,
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


class _LoggingState:
    """Prevents duplicate logging configuration."""

    configured = False


_state = _LoggingState()


# =============================================================================
# MAIN CONFIGURATION FUNCTION
# =============================================================================


def configure_testing_logging() -> None:
    """
    Configure logging specifically for testing environment.

    This sets up logging with DEBUG level and testing-appropriate configuration.
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

    This is the main entry point for logging configuration. Call once at startup.

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
    Normal usage (respects .env configuration):
        >>> from tux.shared.config import CONFIG
        >>> configure_logging(config=CONFIG)

    Override for testing:
        >>> configure_logging(level="DEBUG")
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


# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================


def _configure_level_colors() -> None:
    """Configure custom colors for each log level."""
    for level_name, color in LEVEL_COLORS.items():
        logger.level(level_name, color=color)


def _determine_log_level(level: str | None, config: Config | None) -> str:
    """
    Determine the log level from multiple sources.

    Priority (highest to lowest):
    1. Explicit level parameter
    2. config.LOG_LEVEL (from .env)
    3. config.DEBUG (sets DEBUG)
    4. Default "INFO"

    Parameters
    ----------
    level : str | None
        Explicit level override.
    config : Config | None
        Config instance from .env.

    Returns
    -------
    str
        The determined log level.
    """
    if level:
        return level
    if config and config.LOG_LEVEL and config.LOG_LEVEL != "INFO":
        return config.LOG_LEVEL
    if config and config.DEBUG:
        return "DEBUG"
    return "INFO"


def _add_console_handler(log_level: str) -> None:
    """
    Add console handler with custom formatting.

    Uses a dynamic stderr sink for robustness against stream wrapping
    (e.g., by pytest, IDEs, cloud platforms).

    Parameters
    ----------
    log_level : str
        The minimum log level to display.
    """

    def stderr_sink(message: str) -> None:
        """Dynamically retrieve sys.stderr for robustness."""
        sys.stderr.write(message)

    logger.add(
        stderr_sink,
        format=_format_record,
        level=log_level,
        colorize=True,
        backtrace=True,
        diagnose=True,  # Shows variable values in tracebacks
        enqueue=False,  # Synchronous for console
        catch=True,  # Catch errors in logging itself
    )


# =============================================================================
# CUSTOM LOG FORMATTING
# =============================================================================


def _format_record(record: Any) -> str:
    """
    Format log record with IDE-clickable file paths and proper escaping.

    For tux.* modules: Shows clickable path (src/tux/core/app.py:167)
    For third-party: Shows module:function (urllib3.connectionpool:_make_request:544)

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


# =============================================================================
# THIRD-PARTY LIBRARY LOG INTERCEPTION
# =============================================================================


def _configure_third_party_logging() -> None:
    """
    Configure logging interception for third-party libraries.

    This sets up an InterceptHandler that routes standard library logging
    calls to loguru, maintaining proper source attribution for all logs.

    Process:
    1. Create InterceptHandler to bridge logging -> loguru
    2. Replace root logging handler globally
    3. Configure specific library loggers with InterceptHandler
    4. Set appropriate minimum levels for third-party libraries
    """

    class InterceptHandler(logging.Handler):
        """
        Bridge handler that routes standard logging to loguru.

        Preserves original source information (module, function, line)
        from the logging.LogRecord for accurate log attribution.
        """

        def emit(self, record: logging.LogRecord) -> None:
            """
            Emit a log record to loguru.

            Parameters
            ----------
            record : logging.LogRecord
                The standard library log record to route to loguru.
            """
            # Get loguru level name or fallback to numeric level
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = str(record.levelno)

            # Route to loguru with original source information
            try:
                logger.patch(
                    lambda r: r.update(
                        name=record.name,  # e.g., "discord.gateway"
                        function=record.funcName,  # e.g., "on_ready"
                        line=record.lineno,  # Line number
                    ),
                ).opt(exception=record.exc_info).log(level, "{}", record.getMessage())
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

    Logs the configuration of all known third-party loggers, showing
    which handlers are attached and their current levels.

    This is automatically called when DEBUG level is active.
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


# =============================================================================
# STRUCTURED LOGGING HELPERS
# =============================================================================


class StructuredLogger:
    """Helper class for structured logging with consistent context."""

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
