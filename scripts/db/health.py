"""
Command: db health.

Checks database connection and health status.
"""

import asyncio

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


@app.command(name="health")
def health() -> None:
    """Check database connection and health status."""
    print_section("Database Health", "blue")
    rich_print("[bold blue]Checking database health...[/bold blue]")

    async def _health_check():
        service = DatabaseService(echo=False)
        try:
            with create_progress_bar("Connecting to database...") as progress:
                progress.add_task("Checking database health...", total=None)
                await service.connect(CONFIG.database_url)
                health_data = await service.health_check()

            if health_data["status"] == "healthy":
                rich_print("[green]Database is healthy![/green]")
                rich_print(f"[green]Mode: {health_data.get('mode', 'unknown')}[/green]")
            else:
                rich_print("[red]Database is unhealthy![/red]")
                rich_print(
                    f"[red]Error: {health_data.get('error', 'Unknown error')}[/red]",
                )

            print_success("Health check completed")

        except Exception as e:
            print_error(f"Failed to check database health: {e}")
            raise Exit(1) from e
        finally:
            await service.disconnect()

    asyncio.run(_health_check())


if __name__ == "__main__":
    app()
