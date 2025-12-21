"""
Database Command Group.

Aggregates all database-related operations.
"""

from scripts.core import create_app
from scripts.db import (
    check,
    dev,
    downgrade,
    health,
    history,
    init,
    new,
    nuke,
    push,
    queries,
    reset,
    schema,
    show,
    status,
    tables,
    version,
)

app = create_app(name="db", help_text="Database operations")

app.add_typer(init.app)
app.add_typer(dev.app)
app.add_typer(push.app)
app.add_typer(status.app)
app.add_typer(new.app)
app.add_typer(history.app)
app.add_typer(check.app)
app.add_typer(show.app)
app.add_typer(tables.app)
app.add_typer(health.app)
app.add_typer(schema.app)
app.add_typer(queries.app)
app.add_typer(reset.app)
app.add_typer(downgrade.app)
app.add_typer(nuke.app)
app.add_typer(version.app)


def main() -> None:
    """Entry point for the db command group."""
    app()
