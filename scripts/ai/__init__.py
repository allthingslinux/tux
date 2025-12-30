"""
AI Command Group.

Aggregates AI-related tools and utilities.
"""

from scripts.ai import validate_rules
from scripts.core import create_app

app = create_app(name="ai", help_text="AI tools and utilities")

app.add_typer(validate_rules.app)


def main() -> None:
    """Entry point for the ai command group."""
    app()
