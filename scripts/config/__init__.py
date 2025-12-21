"""
Configuration Command Group.

Aggregates configuration generation and validation tools.
"""

from scripts.config import generate, validate
from scripts.core import create_app

app = create_app(name="config", help_text="Configuration management")

app.add_typer(generate.app)
app.add_typer(validate.app)


def main() -> None:
    """Entry point for the config command group."""
    app()
