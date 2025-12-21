"""
Command: db queries.

Checks for long-running database queries.
"""

import asyncio
from typing import Any

from sqlalchemy import text
from typer import Exit

from scripts.core import create_app
from scripts.ui import (
    create_progress_bar,
    print_error,
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

    async def _check_queries():
        service = DatabaseService(echo=False)
        try:
            with create_progress_bar("Analyzing queries...") as progress:
                progress.add_task("Checking for long-running queries...", total=None)
                await service.connect(CONFIG.database_url)

                async def _get_long_queries(
                    session: Any,
                ) -> list[tuple[Any, Any, str, str]]:
                    result = await session.execute(text(LONG_RUNNING_QUERIES_SQL))
                    return result.fetchall()

                long_queries = await service.execute_query(
                    _get_long_queries,
                    "get_long_queries",
                )

            if long_queries:
                rich_print(
                    f"[yellow]Found {len(long_queries)} long-running queries:[/yellow]",
                )
                for pid, duration, query_text, state in long_queries:
                    rich_print(f"[red]PID {pid}[/red]: {state} for {duration}")
                    query_preview = (
                        (query_text[:100] + "...") if query_text else "<no query text>"
                    )
                    rich_print(f"     Query: {query_preview}")
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
