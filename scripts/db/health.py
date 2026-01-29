"""
Command: db health.

Checks database connection and health status.
Optionally checks Valkey (cache) when VALKEY_URL is configured.
"""

import asyncio

from loguru import logger
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
from tux.cache.service import CacheService
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

app = create_app()


def _fail() -> None:
    """Raise Exit(1) to satisfy Ruff's TRY301 rule."""
    raise Exit(1)


async def _check_cache() -> dict[str, str]:
    """Check Valkey (cache) connection when configured. Return status dict."""
    if not CONFIG.valkey_url:
        logger.debug("Valkey health check: skipped (not configured)")
        return {"status": "skipped", "message": "Valkey not configured"}
    cache_service = CacheService()
    try:
        await cache_service.connect()
        if await cache_service.ping():
            logger.debug("Valkey health check: healthy")
            return {"status": "healthy", "message": "Valkey ping OK"}
        else:  # noqa: RET505
            logger.debug("Valkey health check: ping failed")
            return {"status": "unhealthy", "message": "Valkey ping failed"}
    except Exception as e:
        logger.warning("Valkey health check failed: %s", e)
        return {"status": "unhealthy", "message": str(e)}
    finally:
        await cache_service.close()


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
            else:
                rich_print("[red]Database is unhealthy![/red]")
                rich_print(
                    f"[red]Error: {health_data.get('error', 'Unknown error')}[/red]",
                )
                print_error("Health check failed")
                _fail()

            # Optional: check Valkey when configured
            cache_result = await _check_cache()
            if cache_result["status"] == "skipped":
                rich_print("[dim]Cache (Valkey): not configured, skipping[/dim]")
            elif cache_result["status"] == "healthy":
                rich_print("[green]Cache (Valkey): healthy[/green]")
                print_pretty(cache_result)
            else:
                rich_print("[red]Cache (Valkey): unhealthy[/red]")
                rich_print(
                    f"[red]Error: {cache_result.get('message', 'Unknown')}[/red]",
                )
                print_error("Cache health check failed")
                _fail()

            print_success("Health check completed")

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
