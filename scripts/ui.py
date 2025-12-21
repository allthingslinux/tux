"""
UI Utilities for CLI.

Provides functional helpers for consistent Rich-formatted terminal output.
"""

from typing import Any

from rich.console import Console
from rich.pretty import pprint
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TextColumn,
)
from rich.status import Status
from rich.table import Table

# Shared console instance for all scripts
# We use one instance to avoid interleaving issues when managing the terminal state
console = Console()


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[bold red]✗ Error:[/bold red] {message}")


def print_info(message: str) -> None:
    """Print an info message in blue."""
    console.print(f"[blue]i[/blue] {message}")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_section(title: str, color: str = "blue") -> None:
    """Print a section title."""
    console.print()
    console.print(f"[bold {color}]{title}[/bold {color}]")


def rich_print(message: str) -> None:
    """Print a rich-formatted string directly."""
    console.print(message)


def print_pretty(
    obj: Any,
    expand_all: bool = False,
    max_length: int | None = None,
    indent_guides: bool = True,
) -> None:
    """
    Pretty print a container (list, dict, set, etc.) using Rich.

    Parameters
    ----------
    obj : Any
        The object to pretty print.
    expand_all : bool, optional
        Whether to fully expand all data structures (default is False).
    max_length : int | None, optional
        Maximum number of elements to show before truncating (default is None).
    indent_guides : bool, optional
        Whether to show indent guides (default is True).
    """
    pprint(
        obj,
        expand_all=expand_all,
        max_length=max_length,
        console=console,
        indent_guides=indent_guides,
    )


def print_json(data: str | Any) -> None:
    """
    Pretty print JSON data.

    Parameters
    ----------
    data : str | Any
        The JSON string or object to print.
    """
    if isinstance(data, str):
        console.print_json(data)
    else:
        console.print_json(data=data)


def prompt(message: str, password: bool = False) -> str:
    """
    Prompt the user for input with rich formatting.

    Parameters
    ----------
    message : str
        The prompt message.
    password : bool, optional
        Whether to hide the input (default is False).

    Returns
    -------
    str
        The user's input.
    """
    return console.input(f"[bold blue]?[/bold blue] {message}", password=password)


def create_status(message: str, spinner: str = "dots") -> Status:
    """
    Create a status context manager with a spinner.

    Parameters
    ----------
    message : str
        The message to show next to the spinner.
    spinner : str, optional
        The spinner animation type (default is "dots").

    Returns
    -------
    Status
        A Rich Status context manager.
    """
    return console.status(message, spinner=spinner)


def print_table(
    title: str,
    columns: list[tuple[str, str]],
    data: list[tuple[str, ...]],
) -> None:
    """
    Print a Rich table with title, columns, and data.

    Parameters
    ----------
    title : str
        The title of the table.
    columns : list[tuple[str, str]]
        List of (column_name, style) tuples.
    data : list[tuple[str, ...]]
        List of row tuples.
    """
    table = Table(title=title)
    for column_name, style in columns:
        table.add_column(column_name, style=style)

    for row in data:
        table.add_row(*[str(item) for item in row])

    console.print(table)


def create_progress_bar(
    total: int | None = None,
) -> Progress:
    """
    Create a functional Rich progress bar.

    Parameters
    ----------
    total : int | None, optional
        Total number of steps. If provided, shows percentage and bar.

    Returns
    -------
    Progress
        A configured Progress instance.
    """
    columns: list[ProgressColumn] = [
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ]

    if total is not None:
        columns.extend(
            [
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}% "),
            ],
        )

    columns.append(TextColumn("[progress.elapsed]{task.elapsed:.1f}s "))

    return Progress(
        *columns,
        transient=True,
        console=console,
    )
