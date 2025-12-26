"""
Command: db health.

Checks database connection and health status.
"""

import asyncio

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


def _fail() -> None:
    """Raise Exit(1) to satisfy Ruff's TRY301 rule."""
    raise Exit(1)


@app.command(name="health")
def health() -> None:
    """Check database connection and health status."""
    print_section("Database Health", "blue")
    rich_print("[bold blue]Checking database health...[/bold blue]")

    async def _health_check() -> None:
        service = DatabaseService(echo=False)
        try:
            with create_status("Checking database health...") as status:
                await service.connect(CONFIG.database_url)
                health_data = await service.health_check()
                status.update("[bold green]Connection successful![/bold green]")

            if health_data["status"] == "healthy":
                rich_print("[green]Database is healthy![/green]")
                rich_print(f"[green]Mode: {health_data.get('mode', 'unknown')}[/green]")
                print_pretty(health_data)
                print_success("Health check completed")
            else:
                rich_print("[red]Database is unhealthy![/red]")
                rich_print(
                    f"[red]Error: {health_data.get('error', 'Unknown error')}[/red]",
                )
                print_error("Health check failed")
                _fail()

        except Exception as e:
            if not isinstance(e, Exit):
                print_error(f"Failed to check database health: {e}")
                raise Exit(1) from e
            raise
        finally:
            await service.disconnect()

    asyncio.run(_health_check())


if __name__ == "__main__":
    app()
