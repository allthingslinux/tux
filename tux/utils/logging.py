"""
Rich logging configuration for Tux.

This module sets up global logging configuration using loguru with Rich formatting.
It should be imported and initialized at the start of the application.
"""  # noqa: A005

import re
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

T = TypeVar("T")


def highlight(style: str) -> dict[str, Callable[[Text], Text]]:
    """
    Create a highlighter function for the given style.
    """

    def highlighter(text: Text) -> Text:
        return Text(text.plain, style=style)

    return {"highlighter": highlighter}


class RichHandlerProtocol(Protocol):
    _log_render: LogRender
    formatter: Formatter | None
    console: Console

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    def render_message(self, record: LogRecord, message: str) -> ConsoleRenderable: ...


class LoguruRichHandler(RichHandler, RichHandlerProtocol):
    """
    Enhanced Rich handler for loguru that splits long messages into two lines.

    For messages that fit within the available space (i.e. between the prefix
    and the right-aligned source info), a single line is printed. If the
    message is too long, then:

      - The first line prints as much of the message as possible.
      - The second line starts with a continued prefix that is spaced to match
        the normal prefix and prints the remainder (with the source info right-aligned).

    The normal prefix is:

        █ [HH:MM:SS][LEVEL     ]

    and the continued prefix is:

        █ [CONTINUED           ]
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._last_time: Text | None = None

    def emit(self, record: LogRecord) -> None:
        """Handle log record emission with custom formatting.

        Parameters
        ----------
        record : LogRecord
            The log record to emit

        Notes
        -----
        Formats log records with:
        - Colored level indicator
        - Timestamp
        - Level name
        - Source location
        - Message
        """
        try:
            # Format the message
            message = self.format(record)

            # --- Level symbol and text ---
            level_name = record.levelname.lower()
            level_symbols = {
                "debug": "[bold cyan]█[/]",  # Cyan block for debug
                "info": "[bold blue]█[/]",  # Blue block for info
                "warning": "[bold yellow]█[/]",  # Yellow block for warning
                "error": "[bold red]█[/]",  # Red block for error
                "critical": "[bold red on red]█[/]",  # Red block on red background for critical
                "success": "[bold green]█[/]",  # Green block for success
                "trace": "[dim]█[/]",  # Dim block for trace
            }

            # Get current time
            now = datetime.now(UTC)
            time_text = Text(now.strftime("%H:%M:%S"))
            time_text.stylize("bold")

            # Format level name
            level_text = Text(f"[{level_name.upper():<8}]")
            level_text.stylize(f"bold {level_name}")

            # --- Constants ---
            level_field_width = 7  # Adjust as needed
            symbol = level_symbols.get(level_name, "[bright_black]█[/]")

            # --- First prefix ---
            first_prefix_markup = (
                f"{symbol} "
                + f"[log.time][{datetime.fromtimestamp(record.created, tz=UTC).strftime('%H:%M:%S')}][/]"
                + "[log.bracket][[/]"
                + f"[logging.level.{level_name}]{record.levelname.upper().ljust(level_field_width)}[/]"
                + "[log.bracket]][/]"
                + " "
            )

            # --- Source info ---
            # For example: "run @ main.py:215"
            source_info = (
                f"[dim]{record.funcName}[bright_black] @ [/bright_black]{record.filename}:{record.lineno}[/dim]"
            )

            # --- Continued prefix ---
            continued_prefix_markup = (
                f"{symbol} [log.bracket][[/]"
                + f"[logging.level.info]{'CONTINUED'.ljust(level_field_width + 13)}[/]"
                + "[log.bracket]][/]"
                + " "
            )

            # Convert the formatted message to plain text.
            plain_message = Text.from_markup(message).plain

            # Clean up task names in messages
            if "discord-ext-tasks: " in plain_message:
                # First remove the discord-ext-tasks prefix
                plain_message = plain_message.replace("discord-ext-tasks: ", "")
                # Then trim everything after the dots in task names
                plain_message = re.sub(r"(\w+)\.\w+", r"\1", plain_message)

            # Print first line with source info after log type
            first_line = first_prefix_markup + source_info + " " + plain_message
            self.console.print(first_line, markup=True, highlight=False)

            # If message is long, print continued lines
            if len(plain_message) > 100:  # Arbitrary threshold for line continuation
                continued_message = plain_message[100:]
                while continued_message:
                    chunk, continued_message = continued_message[:100], continued_message[100:]
                    self.console.print(continued_prefix_markup + chunk, markup=True, highlight=False)

        except Exception:
            self.handleError(record)


def setup_logging() -> None:
    """Set up global logging configuration."""
    console = Console(
        force_terminal=True,
        color_system="truecolor",
        width=200,
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

    logger.configure(
        handlers=[
            {
                "sink": LoguruRichHandler(
                    console=console,
                    show_time=False,  # We display time ourselves.
                    show_path=False,
                    rich_tracebacks=True,
                    tracebacks_show_locals=True,
                    log_time_format="[%X]",
                    markup=True,
                    highlighter=None,
                ),
                "format": "{message}",
                "level": "DEBUG",
            },
        ],
    )
