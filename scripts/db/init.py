"""
Command: db init.

Initializes the database with a proper initial migration.
"""

import asyncio
import pathlib

from sqlalchemy import text

from scripts.core import create_app
from scripts.proc import run_command
from scripts.ui import print_error, print_section, print_success, rich_print
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="init")
def init() -> None:
    """Initialize database with proper migration from empty state."""
    print_section("Initialize Database", "green")
    rich_print("[bold green]Initializing database with migrations...[/bold green]")
    rich_print("[yellow]This will create an initial migration file.[/yellow]\n")

    async def _check_tables():
        try:
            service = DatabaseService(echo=False)
            await service.connect(CONFIG.database_url)
            async with service.session() as session:
                result = await session.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name != 'alembic_version'",
                    ),
                )
                table_count = result.scalar() or 0
            await service.disconnect()
        except Exception:
            return 0
        else:
            return table_count

    async def _check_migrations():
        try:
            service = DatabaseService(echo=False)
            await service.connect(CONFIG.database_url)
            async with service.session() as session:
                result = await session.execute(
                    text("SELECT COUNT(*) FROM alembic_version"),
                )
                migration_count = result.scalar() or 0
            await service.disconnect()
        except Exception:
            return 0
        else:
            return migration_count

    table_count = asyncio.run(_check_tables())
    migration_count = asyncio.run(_check_migrations())

    migration_dir = pathlib.Path("src/tux/database/migrations/versions")
    migration_files = list(migration_dir.glob("*.py")) if migration_dir.exists() else []
    migration_file_count = len([f for f in migration_files if f.name != "__init__.py"])

    if table_count > 0 or migration_count > 0 or migration_file_count > 0:
        rich_print(
            f"[red]Database already has {table_count} tables, {migration_count} migrations in DB, and {migration_file_count} migration files![/red]",
        )
        rich_print(
            "[yellow]'db init' only works on completely empty databases with no migration files.[/yellow]",
        )
        return

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

    except Exception:
        print_error("Failed to initialize database")


if __name__ == "__main__":
    app()
