"""
Rich logging configuration for Tux.

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
        try:
            # Get the formatted message from loguru's formatter.
            message = self.format(record)

            # --- Time formatting ---
            time_format: str | Callable[[datetime], Text] | None = (
                None if self.formatter is None else self.formatter.datefmt
            )
            time_format = time_format or self._log_render.time_format
            log_time = datetime.fromtimestamp(record.created, tz=UTC)
            if callable(time_format):
                log_time_str = str(time_format(log_time))
            else:
                log_time_str = log_time.strftime(time_format or "[%X]")

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
            symbol = level_symbols.get(level_name, "[bright_black]█[/]")  # Default gray block

            # --- Constants ---
            level_field_width = 10  # Adjust as needed

            # --- Build the normal prefix ---
            # Example: "█ [02:06:55][INFO      ]"
            first_prefix_markup = (
                f"{symbol} "
                + f"[log.time]{log_time_str}[/]"
                + "[log.bracket][[/]"
                + f"[logging.level.{level_name}]{record.levelname.upper().ljust(level_field_width)}[/]"
                + "[log.bracket]][/]"
                + " "
            )
            first_prefix_plain = Text.from_markup(first_prefix_markup).plain

            # --- Build the continued prefix ---
            # We want the continued prefix to have the same plain-text width as the normal one.
            # The normal prefix width (plain) is:
            #   len(symbol + " ") + (len(log_time_str) + 2) + (LEVEL_FIELD_WIDTH + 2)
            # For the continued prefix we print "CONTINUED" (padded) in a single bracket:
            #   Total width = len(symbol + " ") + (continued_field_width + 2)
            # Setting these equal gives:
            #   continued_field_width = len(log_time_str) + LEVEL_FIELD_WIDTH + 2
            continued_field_width = len(log_time_str) + level_field_width
            continued_prefix_markup = (
                f"{symbol} "
                + "[log.bracket][[/]"
                + f"[logging.level.info]{'CONTINUED'.ljust(continued_field_width)}[/]"
                + "[log.bracket]][/]"
                + " "
            )
            continued_prefix_plain = Text.from_markup(continued_prefix_markup).plain

            # --- Source info ---
            # For example: "run @ main.py:215"
            source_info = (
                f"[dim]{record.funcName}[bright_black] @ [/bright_black]{record.filename}:{record.lineno}[/dim]"
            )
            source_info_plain = Text.from_markup(source_info).plain

            # --- Total width ---
            # Use the console's actual width if available.
            total_width = (self.console.size.width or self.console.width) or 80

            # Convert the formatted message to plain text.
            plain_message = Text.from_markup(message).plain

            # --- One-line vs two-line decision ---
            # For one-line messages, the available space is the total width
            # minus the widths of the normal prefix and the source info.
            available_for_message = total_width - len(first_prefix_plain) - len(source_info_plain)
            if len(plain_message) <= available_for_message:
                # The message fits on one line.
                padded_msg = plain_message.ljust(available_for_message)
                full_line = first_prefix_markup + padded_msg + source_info
                self.console.print(full_line, markup=True, highlight=False)
            else:
                # --- Two-line (continued) layout ---
                # First line: Reserve all space after the normal prefix.
                first_line_area = total_width - len(first_prefix_plain)
                first_line_msg = plain_message[:first_line_area]  # Simply cut off without ellipsis

                # Second line: use the continued prefix and reserve space for the source info.
                second_line_area = total_width - len(continued_prefix_plain) - len(source_info_plain)
                # The remainder of the message is everything after what was printed on the first line.
                remainder_start = first_line_area  # Adjusted to not account for ellipsis
                second_line_msg = plain_message[remainder_start:]
                if len(second_line_msg) > second_line_area:
                    second_line_msg = second_line_msg[:second_line_area]  # Simply cut off without ellipsis
                padded_second_line_msg = second_line_msg.ljust(second_line_area)
                self.console.print(first_prefix_markup + first_line_msg, markup=True, highlight=False)
                self.console.print(
                    continued_prefix_markup + padded_second_line_msg + source_info,
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
                "level": "DEBUG" if Config.DEV else "INFO",
            },
        ],
    )
