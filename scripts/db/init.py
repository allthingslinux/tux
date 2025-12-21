"""
Command: db init.

Initializes the database with a proper initial migration.
"""

import asyncio
import contextlib
import pathlib

from sqlalchemy import text
from typer import Exit

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import (
    print_error,
    print_pretty,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService

app = create_app()


async def _inspect_db_state() -> tuple[int, int]:
    """Return (table_count, migration_count)."""
    service = DatabaseService(echo=False)
    try:
        async with service.session() as session:
            table_result = await session.execute(
                text(
                    """
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_type = 'BASE TABLE'
                      AND table_name != 'alembic_version'
                    """,
                ),
            )
            migration_result = await session.execute(
                text("SELECT COUNT(*) FROM alembic_version"),
            )

            # Move .scalar() calls inside the session context for clarity
            table_count = table_result.scalar() or 0
            migration_count = migration_result.scalar() or 0
    except Exception:
        # Preserve current behavior: treat errors as "0"
        return 0, 0
    finally:
        with contextlib.suppress(Exception):
            await service.disconnect()
    return table_count, migration_count


@app.command(name="init")
def init() -> None:
    """Initialize database with proper migration from empty state."""
    print_section("Initialize Database", "green")
    rich_print("[bold green]Initializing database with migrations...[/bold green]")
    rich_print("[yellow]This will create an initial migration file.[/yellow]\n")

    table_count, migration_count = asyncio.run(_inspect_db_state())

    migration_dir = pathlib.Path("src/tux/database/migrations/versions")
    migration_files = list(migration_dir.glob("*.py")) if migration_dir.exists() else []

    # More explicit migration file filtering
    migration_file_count = len(
        [
            f
            for f in migration_files
            if f.name != "__init__.py" and not f.name.startswith("_")
        ],
    )

    if table_count > 0 or migration_count > 0 or migration_file_count > 0:
        rich_print("[red]Database initialization blocked:[/red]")
        print_pretty(
            {
                "tables": table_count,
                "migrations_in_db": migration_count,
                "migration_files": migration_file_count,
            },
        )
        rich_print(
            "[yellow]'db init' only works on completely empty databases with no migration files.[/yellow]",
        )
        raise Exit(1)

    try:
        rich_print("[blue]Generating initial migration...[/blue]")
        run_command(
            [
                "uv",
                "run",
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "initial schema",
            ],
        )

        rich_print("[blue]Applying initial migration...[/blue]")
        run_command(["uv", "run", "alembic", "upgrade", "head"])

        print_success("Database initialized with migrations")
        rich_print("[green]Ready for development[/green]")

    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
