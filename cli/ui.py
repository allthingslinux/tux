"""Terminal UI utilities for the CLI.

This module provides rich formatting for terminal output.
"""

from rich.console import Console
from rich.table import Table
from rich.text import Text

# Create a shared console instance
console = Console()

# Styles for different types of messages
SUCCESS_STYLE = "bold green"
ERROR_STYLE = "bold red"
WARNING_STYLE = "bold yellow"
INFO_STYLE = "bold blue"


def success(message: str) -> None:
    console.print(f"[{SUCCESS_STYLE}]✓[/] {message}")


def error(message: str) -> None:
    console.print(f"[{ERROR_STYLE}]✗[/] {message}")


def warning(message: str) -> None:
    console.print(f"[{WARNING_STYLE}]![/] {message}")


def info(message: str) -> None:
    console.print(f"[{INFO_STYLE}]i[/] {message}")


def command_header(group_name: str, command_name: str) -> None:
    """Print a header for a command."""
    text = Text()

    text.append("Running ", style="dim")
    text.append(f"{group_name}", style=INFO_STYLE)
    text.append(":")
    text.append(f"{command_name}", style=SUCCESS_STYLE)

    console.print(text)


def command_result(is_success: bool, message: str = "") -> None:
    """Print the result of a command."""

    if is_success:
        if message:
            success(message)

        else:
            success("Command completed successfully")

    elif message:
        error(message)

    else:
        error("Command failed")


def create_table(title: str, columns: list[str]) -> Table:
    """Create a rich table with the given title and columns."""

    table = Table(title=title)

    for column in columns:
        table.add_column(column)

    return table
