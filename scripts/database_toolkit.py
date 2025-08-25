#!/usr/bin/env python3
"""
🛠️ Database Toolkit - Developer Experience Enhancement

Professional database management CLI based on py-pglite patterns.
Provides debugging, analysis, and maintenance capabilities.

Usage:
    python scripts/database_toolkit.py --help
    python scripts/database_toolkit.py analyze-performance
    python scripts/database_toolkit.py explain-query "SELECT * FROM guild WHERE tags @> ARRAY['gaming']"
    python scripts/database_toolkit.py health-check
    python scripts/database_toolkit.py reset-stats
    python scripts/database_toolkit.py migrate
"""

import asyncio
import json

# Add project root to path for imports
import sys
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tux.database.service import DatabaseService

console = Console()


async def get_db_service() -> DatabaseService:
    """Get configured database service."""
    service = DatabaseService(echo=False)
    await service.connect()
    return service


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """🛠️ Professional Database Toolkit for TuxBot"""
    if verbose:
        logger.add(sys.stderr, level="DEBUG")
    console.print("🛠️  [bold blue]TuxBot Database Toolkit[/bold blue]", style="bold")


@cli.command()
async def health_check():
    """🏥 Perform comprehensive database health check."""
    console.print("🔍 Running health check...", style="yellow")

    try:
        service = await get_db_service()
        health = await service.health_check()

        if health["status"] == "healthy":
            console.print("✅ Database is healthy!", style="green")

            table = Table(title="Database Health Status")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            for key, value in health.items():
                if key != "status":
                    table.add_row(key.replace("_", " ").title(), str(value))

            console.print(table)
        else:
            console.print(f"❌ Database unhealthy: {health.get('error', 'Unknown error')}", style="red")

    except Exception as e:
        console.print(f"❌ Health check failed: {e}", style="red")


@cli.command()
async def analyze_performance():
    """📊 Analyze database performance metrics."""
    console.print("📊 Analyzing database performance...", style="yellow")

    try:
        service = await get_db_service()
        metrics = await service.get_database_metrics()

        # Pool metrics
        console.print("\n🔄 [bold]Connection Pool Status[/bold]")
        pool_table = Table()
        pool_table.add_column("Metric", style="cyan")
        pool_table.add_column("Value", style="green")

        for key, value in metrics["pool"].items():
            pool_table.add_row(key.replace("_", " ").title(), str(value))
        console.print(pool_table)

        # Table statistics
        if metrics["tables"]:
            console.print("\n📋 [bold]Table Statistics[/bold]")
            table_stats = Table()
            table_stats.add_column("Table", style="cyan")
            table_stats.add_column("Live Tuples", style="green")
            table_stats.add_column("Inserts", style="blue")
            table_stats.add_column("Updates", style="yellow")
            table_stats.add_column("Deletes", style="red")
            table_stats.add_column("Seq Scans", style="magenta")
            table_stats.add_column("Index Scans", style="bright_green")

            for table in metrics["tables"]:
                table_stats.add_row(
                    table["tablename"],
                    str(table["live_tuples"]),
                    str(table["inserts"]),
                    str(table["updates"]),
                    str(table["deletes"]),
                    str(table["seq_scan"]),
                    str(table["idx_scan"]),
                )
            console.print(table_stats)

        # Database-wide stats
        if metrics["database"]:
            console.print("\n🗄️  [bold]Database Statistics[/bold]")
            db_table = Table()
            db_table.add_column("Metric", style="cyan")
            db_table.add_column("Value", style="green")

            for key, value in metrics["database"].items():
                if value is not None:
                    db_table.add_row(key.replace("_", " ").title(), str(value))
            console.print(db_table)

    except Exception as e:
        console.print(f"❌ Performance analysis failed: {e}", style="red")


@cli.command()
@click.argument("query", type=str)
async def explain_query(query: str):
    """🔍 Analyze query execution plan."""
    console.print(f"🔍 Analyzing query: {query}", style="yellow")

    try:
        service = await get_db_service()
        analysis = await service.analyze_query_performance(query)

        console.print("\n📋 [bold]Query Analysis[/bold]")
        console.print(Syntax(query, "sql", theme="monokai", line_numbers=True))

        plan = analysis["plan"]
        if plan:
            console.print("\n⚡ [bold]Execution Plan[/bold]")
            execution_time = plan.get("Execution Time", "N/A")
            planning_time = plan.get("Planning Time", "N/A")

            console.print(f"Planning Time: {planning_time} ms", style="blue")
            console.print(f"Execution Time: {execution_time} ms", style="green")

            # Pretty print the plan as JSON
            plan_json = json.dumps(plan, indent=2)
            console.print(Syntax(plan_json, "json", theme="monokai", line_numbers=True))
        else:
            console.print("❌ No execution plan available", style="red")

    except Exception as e:
        console.print(f"❌ Query analysis failed: {e}", style="red")


@cli.command()
async def reset_stats():
    """🔄 Reset database statistics counters."""
    console.print("🔄 Resetting database statistics...", style="yellow")

    try:
        service = await get_db_service()
        success = await service.reset_database_stats()

        if success:
            console.print("✅ Database statistics reset successfully!", style="green")
        else:
            console.print("❌ Failed to reset statistics", style="red")

    except Exception as e:
        console.print(f"❌ Statistics reset failed: {e}", style="red")


@cli.command()
async def migrate():
    """🚀 Run database migrations."""
    console.print("🚀 Running database migrations...", style="yellow")

    try:
        service = await get_db_service()
        success = await service.run_migrations()

        if success:
            console.print("✅ Migrations completed successfully!", style="green")
        else:
            console.print("❌ Migrations failed", style="red")

    except Exception as e:
        console.print(f"❌ Migration failed: {e}", style="red")


@cli.command()
@click.option("--table", "-t", help="Specific table to analyze")
async def table_stats(table: str | None = None):
    """📊 Get detailed table statistics."""
    console.print(f"📊 Analyzing table statistics{'for ' + table if table else ''}...", style="yellow")

    try:
        service = await get_db_service()

        # Get statistics for specific models
        controllers = [
            ("guild", service.guild),
            ("guild_config", service.guild_config),
            ("case", service.case),
        ]

        for name, controller in controllers:
            if table and name != table:
                continue

            console.print(f"\n📋 [bold]{name.title()} Table Statistics[/bold]")
            stats = await controller.get_table_statistics()

            if stats:
                stats_table = Table()
                stats_table.add_column("Metric", style="cyan")
                stats_table.add_column("Value", style="green")

                for key, value in stats.items():
                    if value is not None:
                        stats_table.add_row(key.replace("_", " ").title(), str(value))
                console.print(stats_table)
            else:
                console.print(f"❌ No statistics available for {name}", style="red")

    except Exception as e:
        console.print(f"❌ Table statistics failed: {e}", style="red")


@cli.command()
async def demo_advanced_queries():
    """🎮 Demonstrate PostgreSQL advanced features."""
    console.print("🎮 Demonstrating advanced PostgreSQL queries...", style="yellow")

    try:
        service = await get_db_service()
        guild_controller = service.guild

        console.print("\n1️⃣  [bold]JSON Query Demo[/bold]")
        console.print("Searching guilds with specific metadata...")

        # This would work with the enhanced Guild model
        try:
            guilds = await guild_controller.find_with_json_query(
                "metadata",
                "$.settings.auto_mod",
                True,
            )
            console.print(f"Found {len(guilds)} guilds with auto_mod enabled", style="green")
        except Exception as e:
            console.print(f"JSON query demo not available: {e}", style="yellow")

        console.print("\n2️⃣  [bold]Array Query Demo[/bold]")
        console.print("Searching guilds with gaming tag...")

        try:
            guilds = await guild_controller.find_with_array_contains("tags", "gaming")
            console.print(f"Found {len(guilds)} gaming guilds", style="green")
        except Exception as e:
            console.print(f"Array query demo not available: {e}", style="yellow")

        console.print("\n3️⃣  [bold]Performance Analysis Demo[/bold]")
        console.print("Analyzing query performance...")

        try:
            performance = await guild_controller.explain_query_performance()
            console.print("Query performance analysis completed", style="green")
            console.print(f"Model: {performance['model']}")
        except Exception as e:
            console.print(f"Performance demo not available: {e}", style="yellow")

    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")


def main():
    """Main entry point with async support."""

    # Patch click commands to support async
    for command in cli.commands.values():
        if asyncio.iscoroutinefunction(command.callback):
            original_callback = command.callback

            def create_wrapper(callback):
                def wrapper(*args, **kwargs):
                    return asyncio.run(callback(*args, **kwargs))

                return wrapper

            command.callback = create_wrapper(original_callback)

    cli()


if __name__ == "__main__":
    main()
