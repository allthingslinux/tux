"""
Rich Utilities for CLI.

Provides Rich formatting utilities for consistent CLI output.
"""

from rich.console import Console
from rich.progress import BarColumn, Progress, ProgressColumn, SpinnerColumn, TextColumn
from rich.table import Table


class RichCLI:
    """Rich utilities for CLI applications.

    Provides a set of methods for consistent, colorized CLI output using Rich.
    Includes methods for success, error, info, and warning messages, as well
    as table printing and progress bars.

    Attributes
    ----------
    console : Console
        Rich console instance for output formatting.
    """

    def __init__(self):
        """Initialize a RichCLI instance.

        Creates a Rich Console instance for formatted output.
        """
        self.console = Console()

    def print_success(self, message: str) -> None:
        """Print a success message."""
        self.console.print(f"[green]✅ {message}[/green]")

    def print_error(self, message: str) -> None:
        """Print an error message."""
        self.console.print(f"[red]❌ {message}[/red]")

    def print_info(self, message: str) -> None:
        """Print an info message."""
        self.console.print(f"[blue]🗨️ {message}[/blue]")

    def print_warning(self, message: str) -> None:
        """Print a warning message."""
        self.console.print(f"[yellow]⚠️ {message}[/yellow]")

    def print_section(self, title: str, color: str = "blue") -> None:
        """Print a section header."""
        self.console.print(f"\n[bold {color}]{title}[/bold {color}]")

    def rich_print(self, message: str) -> None:
        """Print a rich formatted message."""
        self.console.print(message)

    def print_rich_table(
        self,
        title: str,
        columns: list[tuple[str, str]],
        data: list[tuple[str, ...]],
    ) -> None:
        """Print a Rich table with title, columns, and data."""
        table = Table(title=title)
        for column_name, style in columns:
            table.add_column(column_name, style=style)

        for row in data:
            table.add_row(*[str(item) for item in row])

        self.console.print(table)

    def create_progress_bar(
        self,
        description: str = "Processing...",
        total: int | None = None,
    ) -> Progress:
        """Create a Rich progress bar with spinner and text.

        Returns
        -------
        Progress
            Configured Progress instance.
        """
        # Build columns list conditionally based on whether total is provided
        columns: list[ProgressColumn] = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ]

        # Add progress bar and percentage columns only if total is provided
        if total is not None:
            columns.extend(
                [
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}% "),
                ],
            )

        # Always include elapsed time
        columns.append(TextColumn("[progress.elapsed]{task.elapsed:.1f}s "))

        return Progress(
            *columns,
            transient=False,
            console=self.console,
        )
