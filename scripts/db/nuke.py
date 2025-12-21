"""
Command: db nuke.

Complete database reset (destructive).
"""

import asyncio
import pathlib
import sys
import traceback
from typing import Annotated, Any

from sqlalchemy import text
from typer import Option

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section, print_success, rich_print
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="nuke")
def nuke(
    force: Annotated[
        bool,
        Option("--force", "-f", help="Skip confirmation prompt"),
    ] = False,
    fresh: Annotated[
        bool,
        Option("--fresh", help="Delete all migration files"),
    ] = False,
    yes: Annotated[
        bool,
        Option("--yes", "-y", help="Automatically answer 'yes' to all prompts"),
    ] = False,
) -> None:
    """Complete database reset."""
    print_section("Complete Database Reset", "red")
    rich_print("[bold red]WARNING: This will DELETE ALL DATA[/bold red]")
    rich_print(
        "[red]This operation is destructive. Use only when migrations are broken.[/red]\n",
    )
    rich_print("[yellow]This operation will:[/yellow]")
    rich_print("  1. Drop ALL tables and reset migration tracking")
    rich_print("  2. Leave database completely empty")
    if fresh:
        rich_print("  3. Delete ALL migration files")
    rich_print("")

    if not (force or yes):
        if not sys.stdin.isatty():
            print_error(
                "Cannot run nuke in non-interactive mode without --force or --yes flag",
            )
            return

        response = input("Type 'NUKE' to confirm (case sensitive): ")
        if response != "NUKE":
            print_info("Nuclear reset cancelled")
            return

    async def _nuclear_reset():
        try:
            service = DatabaseService(echo=False)
            await service.connect(CONFIG.database_url)

            async def _drop_all_tables(session: Any) -> None:
                await session.execute(text("DROP TABLE IF EXISTS alembic_version"))
                await session.execute(text("DROP SCHEMA public CASCADE"))
                await session.execute(text("CREATE SCHEMA public"))
                await session.execute(text("GRANT ALL ON SCHEMA public TO public"))
                await session.commit()

            rich_print("[yellow]Dropping all tables and schema...[/yellow]")
            await service.execute_query(_drop_all_tables, "drop_all_tables")
            await service.disconnect()

            print_success("Nuclear reset completed - database is completely empty")

            if fresh:
                migration_dir = pathlib.Path("src/tux/database/migrations/versions")
                if migration_dir.exists():
                    rich_print("[yellow]Deleting all migration files...[/yellow]")
                    deleted_count = 0
                    for migration_file in migration_dir.glob("*.py"):
                        if migration_file.name != "__init__.py":
                            migration_file.unlink()
                            deleted_count += 1
                    print_success(f"Deleted {deleted_count} migration files")

            rich_print("[yellow]Next steps:[/yellow]")
            if fresh:
                rich_print(
                    "  • Run 'uv run db init' to create new initial migration and setup",
                )
            else:
                rich_print(
                    "  • Run 'uv run db push' to recreate tables from existing migrations",
                )
                rich_print(
                    "  • For completely fresh start: delete migration files, then run 'db init'",
                )
            rich_print("  • Or manually recreate tables as needed")

        except Exception as e:
            print_error(f"Failed to nuclear reset database: {e}")
            traceback.print_exc()

    asyncio.run(_nuclear_reset())


if __name__ == "__main__":
    app()
