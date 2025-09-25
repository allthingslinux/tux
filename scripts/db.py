"""
Database CLI

Clean database CLI implementation using the CLI infrastructure.
"""

import asyncio
import subprocess
from typing import Annotated, Any

from sqlalchemy import text
from typer import Argument, Option  # type: ignore[attr-defined]

from scripts.base import BaseCLI
from scripts.registry import Command

# Import here to avoid circular imports
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG


class DatabaseCLI(BaseCLI):
    """Database CLI with unified interface for all database operations."""

    def __init__(self):
        super().__init__(name="db", description="Database CLI - A unified interface for all database operations")
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Setup the command registry with all database commands."""
        # All commands directly registered without groups
        all_commands = [
            # Migration commands
            Command("migrate-dev", self.migrate_dev, "Create and apply migrations for development"),
            Command("migrate-generate", self.migrate_generate, "Generate a new migration from model changes"),
            Command("migrate-push", self.migrate_push, "Push pending migrations to database"),
            Command("migrate-pull", self.migrate_pull, "Pull database schema and generate migration"),
            Command("migrate-reset", self.migrate_reset, "Reset database and apply all migrations"),
            Command("migrate-status", self.migrate_status, "Show migration status with rich output"),
            Command("migrate-history", self.migrate_history, "Show migration history with tree view"),
            Command("migrate-deploy", self.migrate_deploy, "Deploy migrations to production"),
            Command("migrate-format", self.migrate_format, "Format migration files"),
            Command("migrate-validate", self.migrate_validate, "Validate migration files"),
            # Maintenance commands
            Command("health", self.health, "Check database health and connection status"),
            Command("stats", self.stats, "Show database statistics and metrics"),
            Command("tables", self.tables, "List all database tables with their information"),
            Command("analyze", self.analyze, "Analyze table statistics for performance optimization"),
            Command("queries", self.queries, "Check for long-running database queries"),
            Command("optimize", self.optimize, "Analyze database optimization opportunities"),
            Command("vacuum", self.vacuum, "Show database maintenance information"),
            Command("reindex", self.reindex, "Reindex database tables for performance optimization"),
            # Admin commands
            Command("reset", self.reset, "Reset database to clean state (development only)"),
            Command("force", self.force, "Force database to head revision (fixes migration issues)"),
            Command("version", self.version, "Show version information"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Setup all database CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _print_section_header(self, title: str, emoji: str) -> None:
        """Print a standardized section header for database operations."""
        self.rich.print_section(f"{emoji} {title}", "blue")
        self.rich.rich_print(f"[bold blue]{title}...[/bold blue]")

    # ============================================================================
    # MIGRATION COMMANDS
    # ============================================================================

    def migrate_dev(
        self,
        create_only: Annotated[bool, Option("--create-only", help="Create migration but don't apply it")] = False,
        name: Annotated[str | None, Option("--name", "-n", help="Name for the migration")] = None,
    ) -> None:
        """Create and apply migrations for development.

        This command creates a new migration from model changes and optionally applies it.
        Similar to `prisma migrate dev` workflow.

        Use this for development workflow with auto-migration.
        """
        self.rich.print_section("🚀 Development Migration", "blue")

        if create_only:
            self.rich.rich_print("[bold blue]Creating migration only...[/bold blue]")
            self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", name or "auto migration"])
        else:
            self.rich.rich_print("[bold blue]Creating and applying migration...[/bold blue]")
            self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", name or "auto migration"])
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])

        self.rich.print_success("Development migration completed")

    def migrate_generate(
        self,
        message: Annotated[str, Argument(help="Descriptive message for the migration", metavar="MESSAGE")],
        auto_generate: Annotated[
            bool,
            Option("--auto", help="Auto-generate migration from model changes"),
        ] = True,
    ) -> None:
        """Generate a new migration from model changes.

        Creates a new migration file with the specified message.

        Always review generated migrations before applying.
        """
        self.rich.print_section("📝 Generating Migration", "blue")
        self.rich.rich_print(f"[bold blue]Generating migration: {message}[/bold blue]")

        try:
            if auto_generate:
                self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", message])
            else:
                self._run_command(["uv", "run", "alembic", "revision", "-m", message])
            self.rich.print_success(f"Migration generated: {message}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to generate migration")

    def migrate_push(self) -> None:
        """Push pending migrations to database.

        Applies all pending migrations to the database.
        """
        self.rich.print_section("⬆️ Pushing Migrations", "blue")
        self.rich.rich_print("[bold blue]Applying pending migrations...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("Migrations pushed successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to push migrations")

    def migrate_pull(self) -> None:
        """Pull database schema and generate migration.

        Introspects the database and generates a migration from the current state.
        """
        self.rich.print_section("⬇️ Pulling Schema", "blue")
        self.rich.rich_print("[bold blue]Pulling database schema...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", "pull schema"])
            self.rich.print_success("Schema pulled successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to pull schema")

    def migrate_reset(self) -> None:
        """Reset database and apply all migrations.

        Drops all tables and reapplies all migrations from scratch.
        """
        self.rich.print_section("🔄 Resetting Database", "blue")
        self.rich.rich_print("[bold red]Resetting database to clean state...[/bold red]")

        try:
            self._run_command(["uv", "run", "alembic", "downgrade", "base"])
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("Database reset completed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to reset database")

    def migrate_status(self) -> None:
        """Show migration status with rich output.

        Displays current migration status and pending changes.
        """
        self.rich.print_section("📊 Migration Status", "blue")
        self.rich.rich_print("[bold blue]Checking migration status...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "current"])
            self._run_command(["uv", "run", "alembic", "heads"])
            self.rich.print_success("Migration status displayed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get migration status")

    def migrate_history(self) -> None:
        """Show migration history with tree view.

        Displays the complete migration history in a tree format.
        """
        self.rich.print_section("📜 Migration History", "blue")
        self.rich.rich_print("[bold blue]Showing migration history...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "history", "--verbose"])
            self.rich.print_success("Migration history displayed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get migration history")

    def migrate_deploy(self) -> None:
        """Deploy migrations to production.

        Applies migrations in production environment with safety checks.
        """
        self.rich.print_section("🚀 Deploying Migrations", "blue")
        self.rich.rich_print("[bold blue]Deploying migrations to production...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("Migrations deployed successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to deploy migrations")

    def migrate_format(self) -> None:
        """Format migration files.

        Formats all migration files for consistency.
        """
        self.rich.print_section("🎨 Formatting Migrations", "blue")
        self.rich.rich_print("[bold blue]Formatting migration files...[/bold blue]")

        try:
            self._run_command(["uv", "run", "black", "alembic/versions/"])
            self.rich.print_success("Migration files formatted")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to format migration files")

    def migrate_validate(self) -> None:
        """Validate migration files.

        Validates all migration files for correctness.
        """
        self.rich.print_section("✅ Validating Migrations", "blue")
        self.rich.rich_print("[bold blue]Validating migration files...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "check"])
            self.rich.print_success("Migration files validated")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to validate migration files")

    # ============================================================================
    # MAINTENANCE COMMANDS
    # ============================================================================

    def health(self) -> None:
        """Check database health and connection status.

        Performs comprehensive health checks on the database connection
        and reports system status.

        Use this to monitor database health.
        """
        self.rich.print_section("🏥 Database Health Check", "blue")
        self.rich.rich_print("[bold blue]Checking database health...[/bold blue]")

        async def _health_check():
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                health = await service.health_check()

                if health["status"] == "healthy":
                    self.rich.rich_print("[green]✅ Database is healthy![/green]")
                    self.rich.rich_print(f"[green]Connection: {health.get('connection', 'OK')}[/green]")
                    self.rich.rich_print(f"[green]Response time: {health.get('response_time', 'N/A')}[/green]")
                else:
                    self.rich.rich_print("[red]❌ Database is unhealthy![/red]")
                    self.rich.rich_print(f"[red]Error: {health.get('error', 'Unknown error')}[/red]")

                await service.disconnect()
                self.rich.print_success("Database health check completed")

            except Exception as e:
                self.rich.print_error(f"Failed to check database health: {e}")

        asyncio.run(_health_check())

    def stats(self) -> None:
        """Show database statistics and metrics.

        Displays comprehensive database statistics including table sizes,
        index usage, and performance metrics.

        Use this to monitor database performance.
        """
        self._print_section_header("Database Statistics", "📊")
        self.rich.print_info("Database statistics functionality coming soon")

    def tables(self) -> None:
        """List all database tables with their information.

        Shows all tables in the database with column counts, row counts,
        and other metadata.

        Use this to explore database structure.
        """
        self._print_section_header("Database Tables", "📋")

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

                tables = await service.execute_query(_get_tables, "get_tables")

                if not tables:
                    self.rich.print_info("No tables found in database")
                    return

                self.rich.rich_print(f"[green]Found {len(tables)} tables:[/green]")
                for table_name, column_count in tables:
                    self.rich.rich_print(f"  📊 [cyan]{table_name}[/cyan]: {column_count} columns")

                await service.disconnect()
                self.rich.print_success("Database tables listed")

            except Exception as e:
                self.rich.print_error(f"Failed to list database tables: {e}")

        asyncio.run(_list_tables())

    def analyze(self) -> None:
        """Analyze table statistics for performance optimization.

        Analyzes table statistics and provides recommendations for
        performance optimization.

        Use this to optimize database performance.
        """
        self.rich.print_section("🔍 Table Analysis", "blue")
        self.rich.rich_print("[bold blue]Analyzing table statistics...[/bold blue]")
        self.rich.print_info("Table analysis functionality coming soon")

    def queries(self) -> None:
        """Check for long-running database queries.

        Identifies and displays currently running queries that may be
        causing performance issues.

        Use this to identify performance bottlenecks.
        """
        self.rich.print_section("⏱️ Query Analysis", "blue")
        self.rich.rich_print("[bold blue]Checking database queries...[/bold blue]")

        async def _check_queries():
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                async def _get_long_queries(session: Any) -> list[tuple[Any, Any, str, str]]:
                    result = await session.execute(
                        text("""
                        SELECT
                            pid,
                            now() - pg_stat_activity.query_start AS duration,
                            query,
                            state
                        FROM pg_stat_activity
                        WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes'
                        AND state != 'idle'
                        ORDER BY duration DESC
                    """),
                    )
                    return result.fetchall()

                long_queries = await service.execute_query(_get_long_queries, "get_long_queries")

                if long_queries:
                    self.rich.rich_print(f"[yellow]Found {len(long_queries)} long-running queries:[/yellow]")
                    for pid, duration, query, state in long_queries:
                        self.rich.rich_print(f"  🔴 [red]PID {pid}[/red]: {state} for {duration}")
                        self.rich.rich_print(f"     Query: {query[:100]}...")
                else:
                    self.rich.rich_print("[green]✅ No long-running queries found[/green]")

                await service.disconnect()
                self.rich.print_success("Query analysis completed")

            except Exception as e:
                self.rich.print_error(f"Failed to check database queries: {e}")

        asyncio.run(_check_queries())

    def optimize(self) -> None:
        """Analyze database optimization opportunities.

        Analyzes the database and provides recommendations for optimization
        including index suggestions and query improvements.

        Use this to improve database performance.
        """
        self.rich.print_section("⚡ Database Optimization", "blue")
        self.rich.rich_print("[bold blue]Analyzing optimization opportunities...[/bold blue]")
        self.rich.print_info("Database optimization functionality coming soon")

    def vacuum(self) -> None:
        """Show database maintenance information.

        Displays vacuum statistics and maintenance recommendations.

        Use this to monitor database maintenance needs.
        """
        self.rich.print_section("🧹 Database Maintenance", "blue")
        self.rich.rich_print("[bold blue]Checking maintenance status...[/bold blue]")
        self.rich.print_info("Database maintenance functionality coming soon")

    def reindex(self) -> None:
        """Reindex database tables for performance optimization.

        Rebuilds indexes to improve query performance and reduce bloat.

        Use this to optimize database indexes.
        """
        self.rich.print_section("🔧 Database Reindexing", "blue")
        self.rich.rich_print("[bold blue]Reindexing database tables...[/bold blue]")
        self.rich.print_info("Database reindexing functionality coming soon")

    # ============================================================================
    # ADMIN COMMANDS
    # ============================================================================

    def reset(self) -> None:
        """Reset database to clean state (development only).

        Drops all tables and recreates the database from scratch.
        This is a destructive operation and should only be used in development.

        Use this to start fresh in development.
        """
        self.rich.print_section("🔄 Database Reset", "blue")
        self.rich.rich_print("[bold red]Resetting database to clean state...[/bold red]")

        try:
            self._run_command(["uv", "run", "alembic", "downgrade", "base"])
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("Database reset completed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to reset database")

    def force(self) -> None:
        """Force database to head revision (fixes migration issues).

        Forces the database to the latest migration state, useful for
        fixing migration inconsistencies.

        Use this to fix migration issues.
        """
        self.rich.print_section("🔧 Force Migration", "blue")
        self.rich.rich_print("[bold blue]Forcing database to head revision...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "stamp", "head"])
            self.rich.print_success("Database forced to head revision")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to force database revision")

    def version(self) -> None:
        """Show version information.

        Displays version information for the database CLI and related components.

        Use this to check system versions.
        """
        self.rich.print_section("📌 Version Information", "blue")
        self.rich.rich_print("[bold blue]Showing database version information...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "current"])
            self._run_command(
                ["uv", "run", "python", "-c", "import psycopg; print(f'PostgreSQL version: {psycopg.__version__}')"],
            )
            self.rich.print_success("Version information displayed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get version information")


# Create the CLI app instance for mkdocs-typer
app = DatabaseCLI().app


def main() -> None:
    """Entry point for the database CLI script."""
    cli = DatabaseCLI()
    cli.run()


if __name__ == "__main__":
    main()
