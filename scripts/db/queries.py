"""
Command: db queries.

Checks for long-running database queries.
"""

import asyncio
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_status,
    print_error,
    print_pretty,
    print_section,
    print_success,
    rich_print,
)
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()

LONG_RUNNING_QUERIES_SQL = """
SELECT
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
AND state != 'idle'
ORDER BY duration DESC
"""


@app.command(name="queries")
def queries() -> None:
    """Check for long-running database queries."""
    print_section("Query Analysis", "blue")
    rich_print("[bold blue]Checking for long-running queries...[/bold blue]")

    async def _check_queries() -> None:
        service = DatabaseService(echo=False)
        try:
            with create_status("Analyzing queries...") as status:
                await service.connect(CONFIG.database_url)

                async def _get_long_queries(
                    session: AsyncSession,
                ) -> Any:
                    result = await session.execute(text(LONG_RUNNING_QUERIES_SQL))
                    return result.fetchall()

                long_queries = await service.execute_query(
                    _get_long_queries,
                    "get_long_queries",
                )
                status.update("[bold green]Analysis complete![/bold green]")

            if long_queries:
                rich_print(
                    f"[yellow]Found {len(long_queries)} long-running queries:[/yellow]",
                )
                print_pretty(long_queries)
            else:
                rich_print("[green]No long-running queries found[/green]")

            print_success("Query analysis completed")

        except Exception as e:
            print_error(f"Failed to check database queries: {e}")
            raise Exit(1) from e
        finally:
            await service.disconnect()

    asyncio.run(_check_queries())


if __name__ == "__main__":
    app()
