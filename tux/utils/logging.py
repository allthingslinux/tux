"""Rich logging configuration for Tux.

This module sets up global logging configuration using loguru with Rich formatting.
It should be imported and initialized at the start of the application.
"""  # noqa: A005

from collections.abc import Callable
from datetime import UTC, datetime
from logging import Formatter, LogRecord
from typing import Any, Protocol, TypeVar

from loguru import logger
from rich._log_render import LogRender
from rich.console import Console, ConsoleRenderable
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

from tux.utils.config import Config

T = TypeVar("T")


def highlight(style: str) -> dict[str, Callable[[Text], Text]]:
    """
    Create a highlighter function for the given style.

    Parameters
    ----------
    style : str
        The style to apply to the text

    Returns
    -------
    dict[str, Callable[[Text], Text]]
        A dict containing the highlighter function
    """

    def highlighter(text: Text) -> Text:
        return Text(text.plain, style=style)

    return {"highlighter": highlighter}


class RichHandlerProtocol(Protocol):
    _log_render: LogRender
    formatter: Formatter | None
    console: Console

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    """
    Initialize the Rich handler.

    Parameters
    ----------
    *args : Any
        The arguments to pass to the RichHandler constructor
    **kwargs : Any
        The keyword arguments to pass to the RichHandler constructor
    """

    def render_message(self, record: LogRecord, message: str) -> ConsoleRenderable: ...


class LoguruRichHandler(RichHandler, RichHandlerProtocol):
    """
    Enhanced Rich handler for loguru that supports better styling and formatting.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the Rich handler.

        Parameters
        ----------
        *args : Any
            The arguments to pass to the RichHandler constructor
        **kwargs : Any
            The keyword arguments to pass to the RichHandler constructor
        """
        super().__init__(*args, **kwargs)
        self._last_time: Text | None = None

    def emit(self, record: LogRecord) -> None:
        """
        Emit a log record.

        Parameters
        ----------
        record : LogRecord
            The log record to emit.
        """
        try:
            # Get the formatted message
            message = self.format(record)

            # Handle time formatting
            time_format: str | Callable[[datetime], Text] | None = (
                None if self.formatter is None else self.formatter.datefmt
            )
            time_format = time_format or self._log_render.time_format
            log_time = datetime.fromtimestamp(record.created, tz=UTC)

            # Handle callable time format
            if callable(time_format):
                log_time_str = str(time_format(log_time))
            else:
                log_time_str = log_time.strftime(time_format or "[%X]")

            # Format the level with symbols
            level_name = record.levelname.lower()
            level_symbols = {
                "debug": "[bold cyan]█[/]",  # Cyan block for debug
                "info": "[bold blue]█[/]",  # Blue block for info
                "warning": "[bold yellow]█[/]",  # Yellow block for warning
                "error": "[bold red]█[/]",  # Red block for error
                "critical": "[bold red on red]█[/]",  # Red block on red bg for critical
                "success": "[bold green]█[/]",  # Green block for success
                "trace": "[dim]█[/]",  # Dim block for trace
            }
            symbol = level_symbols.get(level_name, "[bright_black]█[/]")  # Gray block for default
            level_str = f"{record.levelname:<7}"  # Reduced padding by 1

            # Format source info and display it as part of the log prefix (before the actual message)
            source_info = (
                f"[dim]{record.funcName}[bright_black] @ [/bright_black]{record.filename}:{record.lineno}[/dim]"
            )

            log_prefix = (
                f"{symbol} [log.time]{log_time_str}[/]"
                f"[log.bracket][[/][logging.level.{level_name}]{level_str}[/][log.bracket]][/] "
                f"{source_info} "
            )

            # Print the complete log line with the source info preceding the actual log message.
            self.console.print(
                f"{log_prefix}{message}",
                markup=True,
                highlight=False,
            )
        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """Set up global logging configuration."""
    console = Console(
        force_terminal=True,
        color_system="truecolor",
        theme=Theme(
            {
                "logging.level.success": "bold green",
                "logging.level.trace": "dim",
                "logging.level.debug": "bold cyan",
                "logging.level.info": "bold blue",
                "logging.level.warning": "bold yellow",
                "logging.level.error": "bold red",
                "logging.level.critical": "bold red reverse",
                "log.time": "bold bright_white",
                "log.bracket": "bold bright_black",
            },
        ),
    )

    # Configure loguru with Rich handler
    logger.configure(
        handlers=[
            {
                "sink": LoguruRichHandler(
                    console=console,
                    show_time=False,  # We handle time display ourselves
                    show_path=False,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    log_time_format="[%X]",
                    markup=True,
                    highlighter=None,  # Disable automatic highlighting
                ),
                "format": "{message}",  # Just the message since we handle the rest
                "level": "DEBUG" if Config.DEV else "INFO",
            },
        ],
    )
