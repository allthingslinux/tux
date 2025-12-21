"""
Command: db tables.

Lists all database tables and their structure.
"""

import asyncio
from typing import Any

from sqlalchemy import text

from scripts.core import create_app
from scripts.ui import print_error, print_info, print_section, print_success, rich_print
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


@app.command(name="tables")
def tables() -> None:
    """List all database tables and their structure."""
    print_section("Database Tables", "blue")
    rich_print("[bold blue]Listing database tables...[/bold blue]")

    async def _list_tables():
        try:
            service = DatabaseService(echo=False)
            await service.connect(CONFIG.database_url)

            async def _get_tables(session: Any) -> list[tuple[str, int]]:
                result = await session.execute(
                    text("""
                    SELECT
                        table_name,
                        (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
                    FROM information_schema.tables t
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    AND table_name != 'alembic_version'
                    ORDER BY table_name
                """),
                )
                return result.fetchall()

            tables_data = await service.execute_query(_get_tables, "get_tables")

            if not tables_data:
                print_info("No tables found in database")
                return

            rich_print(f"[green]Found {len(tables_data)} tables:[/green]")
            for table_name, column_count in tables_data:
                rich_print(f"[cyan]{table_name}[/cyan]: {column_count} columns")

            await service.disconnect()
            print_success("Database tables listed")

        except Exception as e:
            print_error(f"Failed to list database tables: {e}")

    asyncio.run(_list_tables())


if __name__ == "__main__":
    app()
