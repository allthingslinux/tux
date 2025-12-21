"""
Tux Command Group.

Aggregates all bot-related operations.
"""

from scripts.core import create_app
from scripts.tux import start, version

app = create_app(name="tux", help_text="Bot operations")

app.add_typer(start.app)
app.add_typer(version.app)


def main() -> None:
    """Entry point for the tux command group."""
    app()
