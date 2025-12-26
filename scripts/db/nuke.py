"""
Command: db nuke.

Complete database reset (destructive).
"""

import asyncio
import os
import sys
import traceback
from typing import Annotated

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from typer import Exit, Option

from scripts.core import ROOT, create_app
from scripts.ui import (
    print_error,
    print_info,
    print_section,
    print_success,
    print_warning,
    prompt,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


async def _drop_and_recreate_schema(session: AsyncSession) -> None:
    """Drop the public schema (including all tables) and recreate it."""
    # Dropping the schema with CASCADE will already drop all tables including alembic_version
    await session.execute(text("DROP SCHEMA public CASCADE"))
    await session.execute(text("CREATE SCHEMA public"))
    # Note: We removed GRANT ALL ON SCHEMA public TO public for security reasons.
    # The connection user should already have necessary permissions as owner.


def _delete_migration_files() -> None:
    """Delete all migration files in the versions directory."""
    # Anchor to repo root via ROOT constant from core
    migration_dir = ROOT / "src" / "tux" / "database" / "migrations" / "versions"
    if migration_dir.exists():
        rich_print("[yellow]Deleting all migration files...[/yellow]")
        deleted_count = 0
        for migration_file in migration_dir.glob("*.py"):
            if migration_file.name != "__init__.py":
                try:
                    migration_file.unlink()
                    deleted_count += 1
                except OSError as e:
                    print_error(f"Failed to delete {migration_file.name}: {e}")
        print_success(f"Deleted {deleted_count} migration files")
    else:
        print_error(f"Migration directory not found: {migration_dir}")
        raise Exit(1)


async def _nuclear_reset(fresh: bool) -> None:
    """Perform a complete database reset by dropping all tables and schemas."""
    # Safety check: prevent running against production
    is_prod = (
        os.getenv("ENVIRONMENT", "").lower() == "production"
        or os.getenv("APP_ENV", "").lower() == "production"
        or getattr(CONFIG, "PRODUCTION", False)
    )

    db_url = CONFIG.database_url
    # Allow override via env var
    prod_keywords = os.getenv("PROD_DB_KEYWORDS", "prod,live,allthingslinux.org").split(
        ",",
    )
    is_prod_db = any(kw.strip() in db_url.lower() for kw in prod_keywords if kw.strip())

    if is_prod or is_prod_db:
        if os.getenv("FORCE_NUKE") != "true":
            print_error(
                "CRITICAL: Cannot run nuke command against production database!",
            )
            rich_print(
                "[yellow]If you are absolutely sure, set FORCE_NUKE=true environment variable.[/yellow]",
            )
            raise Exit(1)
        print_warning(
            "FORCE_NUKE detected. Proceeding with nuclear reset on PRODUCTION database...",
        )

    service = DatabaseService(echo=False)
    try:
        await service.connect(CONFIG.database_url)

        # Show which database is being nuked for user awareness
        db_name = CONFIG.database_url.split("/")[-1].split("?")[0]
        rich_print(f"[yellow]Target database: {db_name}[/yellow]")

        rich_print("[yellow]Dropping all tables and schema...[/yellow]")
        await service.execute_query(
            _drop_and_recreate_schema,
            "drop_and_recreate_schema",
        )

        print_success("Nuclear reset completed - database is completely empty")

        if fresh:
            _delete_migration_files()

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
        raise Exit(1) from e
    finally:
        await service.disconnect()


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
    """
    Complete database reset.

    This command is destructive and should only be used in development
    or in case of critical migration failure.
    """
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
            raise Exit(1)

        response = prompt("Type 'NUKE' to confirm (case sensitive): ")
        if response != "NUKE":
            print_info("Nuclear reset cancelled")
            return

    asyncio.run(_nuclear_reset(fresh))


if __name__ == "__main__":
    app()
