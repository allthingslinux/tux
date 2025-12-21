"""
UI Utilities for CLI.

Provides functional helpers for consistent Rich-formatted terminal output.
"""

from rich.console import Console
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TextColumn
from rich.table import Table

# Shared console instance for all scripts
console = Console()


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]{message}[/green]")


def print_error(message: str) -> None:
    """Print an error message in red."""
    console.print(f"[red]{message}[/red]")


def print_info(message: str) -> None:
    """Print an info message in blue."""
    console.print(f"[blue]{message}[/blue]")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[yellow]{message}[/yellow]")


def print_section(title: str, color: str = "blue") -> None:
    """Print a bold section header with optional color."""
    console.print(f"\n[bold {color}]{title}[/bold {color}]")


def rich_print(message: str) -> None:
    """Print a rich-formatted string directly."""
    console.print(message)


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
    description: str = "Processing...",
    total: int | None = None,
) -> Progress:
    """
    Create a functional Rich progress bar.

    Parameters
    ----------
    description : str, optional
        Text to show next to the progress bar.
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
        transient=False,
        console=console,
    )
