"""
Command: db tables.

Lists all database tables and their structure.
"""

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_progress_bar,
    print_error,
    print_info,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="tables")
def tables() -> None:
    """List all database tables and their structure."""
    print_section("Database Tables", "blue")
    rich_print("[bold blue]Listing database tables...[/bold blue]")

    async def _list_tables() -> None:
        service = DatabaseService(echo=False)
        try:
            await service.connect(CONFIG.database_url)

            async def _get_tables(session: AsyncSession) -> Any:
                result = await session.execute(
                    text("""
                    SELECT
                        table_name,
                        (SELECT COUNT(*) FROM information_schema.columns c
                         WHERE c.table_name = t.table_name
                         AND c.table_schema = t.table_schema) as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    AND table_name != 'alembic_version'
                    ORDER BY table_name
                """),
                )
                return result.fetchall()

            with create_progress_bar(total=None) as progress:
                progress.add_task("Fetching tables...", total=None)
                tables_data = await service.execute_query(_get_tables, "get_tables")

            if not tables_data:
                print_info("No tables found in database")
                return

            rich_print(f"[green]Found {len(tables_data)} tables:[/green]\n")
            max_name_len = (
                max(len(name) for name, _ in tables_data) if tables_data else 0
            )
            width = max(max_name_len, 10)  # minimum 10 chars

            for table_name, column_count in tables_data:
                rich_print(
                    f"  [cyan]{table_name:{width}}[/cyan] {column_count:3} columns",
                )

            print_success("Database tables listed")

        except Exception as e:
            print_error(f"Failed to list database tables: {e}")
            raise Exit(1) from e
        finally:
            await service.disconnect()

    asyncio.run(_list_tables())


if __name__ == "__main__":
    app()
