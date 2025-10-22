"""
Database CLI.

Simple and clean database CLI for SQLModel + Alembic development.
Provides essential commands for database management with clear workflows.
"""

import asyncio
import pathlib
import subprocess
import sys
import traceback
from typing import Annotated, Any

import typer
from sqlalchemy import text
from typer import Argument, Option  # type: ignore[attr-defined]

from scripts.base import BaseCLI
from scripts.registry import Command

# Import here to avoid circular imports
from tux.database.service import DatabaseService
from tux.shared.config import CONFIG


class DatabaseCLI(BaseCLI):
    """Database CLI with clean, workflow-focused commands for SQLModel + Alembic.

    Provides essential database management commands for development and deployment,
    including migration management, database inspection, and administrative operations.
    """

    def __init__(self):
        """Initialize the DatabaseCLI application.

        Sets up the CLI with database-specific commands and configures
        the command registry for database operations.
        """
        super().__init__(name="db", description="Database CLI - Clean commands for SQLModel + Alembic")
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with clean database commands."""
        all_commands = [
            # ============================================================================
            # CORE WORKFLOW COMMANDS
            # ============================================================================
            Command("init", self.init, "Initialize database with proper migrations (recommended for new projects)"),
            Command("dev", self.dev, "Development workflow: generate migration and apply it"),
            Command("push", self.push, "Apply all pending migrations to database"),
            Command("status", self.status, "Show current migration status"),
            # ============================================================================
            # MIGRATION MANAGEMENT
            # ============================================================================
            Command("new", self.new_migration, "Generate new migration from model changes"),
            Command("history", self.history, "Show migration history"),
            Command("check", self.check_migrations, "Validate migration files for issues"),
            Command("show", self.show_migration, "Show details of a specific migration"),
            # ============================================================================
            # DATABASE INSPECTION
            # ============================================================================
            Command("tables", self.tables, "List all database tables"),
            Command("health", self.health, "Check database connection health"),
            Command("queries", self.queries, "Check for long-running queries"),
            # ============================================================================
            # ADMIN COMMANDS
            # ============================================================================
            Command("reset", self.reset, "Reset database to clean state (safe)"),
            Command("downgrade", self.downgrade, "Rollback to a previous migration revision"),
            Command("nuke", self.hard_reset, "Nuclear reset: completely destroy database (dangerous)"),
            Command("version", self.version, "Show version information"),
        ]

        # Note: Some useful alembic commands that are available but not exposed:
        # - branches: Show branch points (advanced scenarios)
        # - edit: Edit migration files (advanced users)
        # - ensure_version: Create alembic_version table if missing
        # - merge: Merge migration branches (advanced scenarios)

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all database CLI commands using the command registry."""
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
    # INITIALIZATION COMMANDS
    # ============================================================================

    def init(self) -> None:
        """Initialize database with proper migration from empty state.

        This is the RECOMMENDED way to set up migrations for a new project.
        Creates a clean initial migration that contains all table creation SQL.

        Workflow:
        1. Ensures database is empty
        2. Generates initial migration with CREATE TABLE statements
        3. Applies the migration

        Use this for new projects or when you want proper migration files.
        """
        self.rich.print_section("🚀 Initialize Database", "green")
        self.rich.rich_print("[bold green]Initializing database with proper migrations...[/bold green]")
        self.rich.rich_print("[yellow]This will create a clean initial migration file.[/yellow]")
        self.rich.rich_print("")

        # Check if tables exist
        async def _check_tables():
            """Check if any tables exist in the database.

            Returns
            -------
            int
                Number of tables found, or 0 if database is empty or inaccessible.
            """
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                # Query directly to avoid error logging for fresh database checks
                async with service.session() as session:
                    result = await session.execute(
                        text(
                            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' AND table_name != 'alembic_version'",
                        ),
                    )
                    table_count = result.scalar() or 0

                await service.disconnect()
            except Exception:
                return 0
            else:
                return table_count

        table_count = asyncio.run(_check_tables())

        # Check if alembic_version table exists (indicating migrations are already set up)
        async def _check_migrations():
            """Check if migrations have been initialized in the database.

            Returns
            -------
            int
                Number of migration records found, or 0 if migrations are not initialized.
            """
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                # Query directly to avoid error logging for expected table-not-found errors
                async with service.session() as session:
                    result = await session.execute(text("SELECT COUNT(*) FROM alembic_version"))
                    migration_count = result.scalar() or 0

                await service.disconnect()
            except Exception:
                # Expected on fresh database - alembic_version table doesn't exist yet
                return 0
            else:
                return migration_count

        migration_count = asyncio.run(_check_migrations())

        # Check if migration files already exist
        migration_dir = pathlib.Path("src/tux/database/migrations/versions")
        migration_files = list(migration_dir.glob("*.py")) if migration_dir.exists() else []
        # Exclude __init__.py from count as it's just a package marker
        migration_file_count = len([f for f in migration_files if f.name != "__init__.py"])

        if table_count > 0 or migration_count > 0 or migration_file_count > 0:
            self.rich.rich_print(
                f"[red]⚠️  Database already has {table_count} tables, {migration_count} migrations in DB, and {migration_file_count} migration files![/red]",
            )
            self.rich.rich_print(
                "[yellow]'db init' only works on completely empty databases with no migration files.[/yellow]",
            )
            self.rich.rich_print(
                "[yellow]For existing databases, use 'db nuke --force' to reset the database completely.[/yellow]",
            )
            self.rich.rich_print(
                "[yellow]Use 'db nuke --force --fresh' for a complete fresh start (deletes migration files too).[/yellow]",
            )
            self.rich.rich_print("[yellow]Or work with your current database state using other commands.[/yellow]")
            return

        # Generate initial migration
        try:
            self.rich.rich_print("[blue]Generating initial migration...[/blue]")
            self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", "initial schema"])

            self.rich.rich_print("[blue]Applying initial migration...[/blue]")
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])

            self.rich.print_success("Database initialized with proper migrations!")
            self.rich.rich_print("[green]✅ Ready for development![/green]")

        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to initialize database")

    # ============================================================================
    # DEVELOPMENT WORKFLOW COMMANDS
    # ============================================================================

    def dev(
        self,
        create_only: Annotated[bool, Option("--create-only", help="Create migration but don't apply it")] = False,
        name: Annotated[str | None, Option("--name", "-n", help="Name for the migration")] = None,
    ) -> None:
        """Development workflow: create migration and apply it.

        Similar to `prisma migrate dev` - creates a new migration from model changes
        and optionally applies it immediately.

        Examples
        --------
        uv run db dev                           # Create + apply with auto-generated name
        uv run db dev --name "add user model"   # Create + apply with custom name
        uv run db dev --create-only             # Create only, don't apply

        Raises
        ------
        Exit
            If migration creation fails.
        """
        self.rich.print_section("🚀 Development Workflow", "blue")

        try:
            if create_only:
                self.rich.rich_print("[bold blue]Creating migration only...[/bold blue]")
                self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", name or "dev migration"])
                self.rich.print_success("Migration created - review and apply with 'db push'")
            else:
                self.rich.rich_print("[bold blue]Creating and applying migration...[/bold blue]")
                self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", name or "dev migration"])
                self._run_command(["uv", "run", "alembic", "upgrade", "head"])
                self.rich.print_success("Migration created and applied!")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to create migration")
            raise typer.Exit(1) from None

    def push(self) -> None:
        """Apply pending migrations to database.

        Applies all pending migrations to bring the database up to date.
        Safe to run multiple times - only applies what's needed.
        """
        self.rich.print_section("⬆️ Apply Migrations", "blue")
        self.rich.rich_print("[bold blue]Applying pending migrations...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("All migrations applied!")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to apply migrations")

    def status(self) -> None:
        """Show current migration status and pending changes.

        Displays:
        - Current migration revision
        - Available migration heads
        - Any pending migrations to apply
        """
        self.rich.print_section("📊 Migration Status", "blue")
        self.rich.rich_print("[bold blue]Checking migration status...[/bold blue]")

        try:
            self.rich.rich_print("[cyan]Current revision:[/cyan]")
            self._run_command(["uv", "run", "alembic", "current"])

            self.rich.rich_print("[cyan]Available heads:[/cyan]")
            self._run_command(["uv", "run", "alembic", "heads"])

            self.rich.print_success("Status check complete")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get migration status")

    # ============================================================================
    # MIGRATION MANAGEMENT COMMANDS
    # ============================================================================

    def new_migration(
        self,
        message: Annotated[str, Argument(help="Descriptive message for the migration", metavar="MESSAGE")],
        auto_generate: Annotated[
            bool,
            Option("--auto", help="Auto-generate migration from model changes"),
        ] = True,
    ) -> None:
        """Generate new migration from model changes.

        Creates a new migration file with the specified message.
        Always review generated migrations before applying them.

        Examples
        --------
        uv run db new "add user email field"        # Auto-generate from model changes
        uv run db new "custom migration" --no-auto  # Empty migration for manual edits

        Raises
        ------
        Exit
            If migration generation fails.
        """
        self.rich.print_section("📝 New Migration", "blue")
        self.rich.rich_print(f"[bold blue]Generating migration: {message}[/bold blue]")

        try:
            if auto_generate:
                self._run_command(["uv", "run", "alembic", "revision", "--autogenerate", "-m", message])
            else:
                self._run_command(["uv", "run", "alembic", "revision", "-m", message])
            self.rich.print_success(f"Migration generated: {message}")
            self.rich.rich_print("[yellow]💡 Review the migration file before applying![/yellow]")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to generate migration")
            raise typer.Exit(1) from None

    def history(self) -> None:
        """Show migration history with detailed tree view.

        Displays the complete migration history in a tree format
        showing revision relationships and messages.
        """
        self.rich.print_section("📜 Migration History", "blue")
        self.rich.rich_print("[bold blue]Showing migration history...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "history", "--verbose"])
            self.rich.print_success("History displayed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get migration history")

    def check_migrations(self) -> None:
        """Validate migration files for correctness.

        Checks that all migration files are properly formatted and
        can be applied without conflicts. Useful before deployments.
        """
        self.rich.print_section("✅ Validate Migrations", "blue")
        self.rich.rich_print("[bold blue]Checking migration files for issues...[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "check"])
            self.rich.print_success("All migrations validated successfully!")
        except subprocess.CalledProcessError:
            self.rich.print_error("Migration validation failed - check your migration files")

    def show_migration(
        self,
        revision: Annotated[str, Argument(help="Migration revision ID to show (e.g., 'head', 'base', or specific ID)")],
    ) -> None:
        """Show details of a specific migration.

        Displays the full details of a migration including its changes,
        dependencies, and metadata.

        Examples
        --------
        uv run db show head          # Show latest migration
        uv run db show base          # Show base revision
        uv run db show abc123        # Show specific migration
        """
        self.rich.print_section("📋 Show Migration", "blue")
        self.rich.rich_print(f"[bold blue]Showing migration: {revision}[/bold blue]")

        try:
            self._run_command(["uv", "run", "alembic", "show", revision])
            self.rich.print_success(f"Migration details displayed for: {revision}")
        except subprocess.CalledProcessError:
            self.rich.print_error(f"Failed to show migration: {revision}")

    # ============================================================================
    # INSPECTION COMMANDS
    # ============================================================================

    def tables(self) -> None:
        """List all database tables and their structure.

        Shows all tables in the database with column counts and basic metadata.
        Useful for exploring database structure and verifying migrations.
        """
        self._print_section_header("Database Tables", "📋")

        async def _list_tables():
            """List all database tables with their metadata."""
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                async def _get_tables(session: Any) -> list[tuple[str, int]]:
                    """Get list of tables with their column counts.

                    Parameters
                    ----------
                    session : Any
                        Database session object.

                    Returns
                    -------
                    list[tuple[str, int]]
                        List of (table_name, column_count) tuples.
                    """
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

    def health(self) -> None:
        """Check database connection and health status.

        Performs health checks on the database connection and reports
        connection status and response times.
        """
        self.rich.print_section("🏥 Database Health", "blue")
        self.rich.rich_print("[bold blue]Checking database health...[/bold blue]")

        async def _health_check():
            """Check the health status of the database connection."""
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
                self.rich.print_success("Health check completed")

            except Exception as e:
                self.rich.print_error(f"Failed to check database health: {e}")

        asyncio.run(_health_check())

    def queries(self) -> None:
        """Check for long-running database queries.

        Identifies and displays currently running queries that may be
        causing performance issues or blocking operations.
        """
        self.rich.print_section("⏱️ Query Analysis", "blue")
        self.rich.rich_print("[bold blue]Checking for long-running queries...[/bold blue]")

        async def _check_queries():
            """Check for long-running queries in the database."""
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                async def _get_long_queries(session: Any) -> list[tuple[Any, Any, str, str]]:
                    """Get list of queries running longer than 5 minutes.

                    Parameters
                    ----------
                    session : Any
                        Database session object.

                    Returns
                    -------
                    list[tuple[Any, Any, str, str]]
                        List of (pid, duration, query, state) tuples for long-running queries.
                    """
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

    # ============================================================================
    # ADMIN COMMANDS
    # ============================================================================

    def reset(self) -> None:
        """Reset database to clean state via migrations.

        Resets the database by downgrading to base (empty) and then
        reapplying all migrations from scratch. Preserves migration files.

        Use this to test the full migration chain or fix migration issues.
        """
        self.rich.print_section("🔄 Reset Database", "yellow")
        self.rich.rich_print("[bold yellow]⚠️  This will reset your database![/bold yellow]")
        self.rich.rich_print("[yellow]Downgrading to base and reapplying all migrations...[/yellow]")

        try:
            self._run_command(["uv", "run", "alembic", "downgrade", "base"])
            self._run_command(["uv", "run", "alembic", "upgrade", "head"])
            self.rich.print_success("Database reset and migrations reapplied!")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to reset database")

    def hard_reset(  # noqa: PLR0915
        self,
        force: Annotated[bool, Option("--force", "-f", help="Skip confirmation prompt")] = False,
        fresh: Annotated[
            bool,
            Option("--fresh", help="Also delete all migration files for complete fresh start"),
        ] = False,
    ) -> None:
        """Nuclear reset: completely destroy the database.

        🚨 DANGER: This is extremely destructive!

        This command will:
        1. Drop ALL tables and alembic tracking
        2. Leave database completely empty
        3. With --fresh: Also delete ALL migration files

        ⚠️  WARNING: This will DELETE ALL DATA permanently!
        Only use this when you want to start completely from scratch.

        After nuking, run 'db push' to recreate tables from existing migrations.
        With --fresh, run 'db init' to create new migrations from scratch.

        For normal development, use 'db reset' instead.
        """
        self.rich.print_section("💥 Nuclear Reset", "red")
        self.rich.rich_print("[bold red]🚨 DANGER: This will DELETE ALL DATA![/bold red]")
        self.rich.rich_print("[red]This is extremely destructive - only use when migrations are broken![/red]")
        self.rich.rich_print("")
        self.rich.rich_print("[yellow]This operation will:[/yellow]")
        self.rich.rich_print("  1. Drop ALL tables and reset migration tracking")
        self.rich.rich_print("  2. Leave database completely empty")
        if fresh:
            self.rich.rich_print("  3. Delete ALL migration files")
        self.rich.rich_print("")

        # Require explicit confirmation unless --force is used
        if not force:
            if not sys.stdin.isatty():
                self.rich.print_error("Cannot run nuke in non-interactive mode without --force flag")
                return

            response = input("Type 'NUKE' to confirm (case sensitive): ")
            if response != "NUKE":
                self.rich.print_info("Nuclear reset cancelled")
                return

        async def _nuclear_reset():
            """Perform a complete database reset by dropping all tables and schemas."""
            try:
                service = DatabaseService(echo=False)
                await service.connect(CONFIG.database_url)

                # Drop all tables including alembic_version
                async def _drop_all_tables(session: Any) -> None:
                    """Drop all tables and recreate the public schema.

                    Parameters
                    ----------
                    session : Any
                        Database session object.
                    """
                    # Explicitly drop alembic_version first (it may not be in public schema)
                    await session.execute(text("DROP TABLE IF EXISTS alembic_version"))
                    # Drop the entire public schema
                    await session.execute(text("DROP SCHEMA public CASCADE"))
                    await session.execute(text("CREATE SCHEMA public"))
                    await session.execute(text("GRANT ALL ON SCHEMA public TO public"))
                    await session.commit()

                self.rich.rich_print("[yellow]Dropping all tables and schema...[/yellow]")
                await service.execute_query(_drop_all_tables, "drop_all_tables")
                await service.disconnect()

                self.rich.print_success("Nuclear reset completed - database is completely empty")

                # Delete migration files if --fresh flag is used
                if fresh:
                    migration_dir = pathlib.Path("src/tux/database/migrations/versions")
                    if migration_dir.exists():
                        self.rich.rich_print("[yellow]Deleting all migration files...[/yellow]")
                        deleted_count = 0
                        for migration_file in migration_dir.glob("*.py"):
                            if migration_file.name != "__init__.py":  # Keep __init__.py
                                migration_file.unlink()
                                deleted_count += 1
                        self.rich.print_success(f"Deleted {deleted_count} migration files")

                self.rich.rich_print("[yellow]Next steps:[/yellow]")
                if fresh:
                    self.rich.rich_print("  • Run 'db init' to create new initial migration and setup")
                else:
                    self.rich.rich_print("  • Run 'db push' to recreate tables from existing migrations")
                    self.rich.rich_print("  • For completely fresh start: delete migration files, then run 'db init'")
                self.rich.rich_print("  • Or manually recreate tables as needed")

            except Exception as e:
                self.rich.print_error(f"Failed to nuclear reset database: {e}")
                traceback.print_exc()

        asyncio.run(_nuclear_reset())

    def downgrade(
        self,
        revision: Annotated[
            str,
            Argument(
                help="Revision to downgrade to (e.g., '-1' for one step back, 'base' for initial state, or specific revision ID)",
            ),
        ],
    ) -> None:
        """Rollback to a previous migration revision.

        Reverts the database schema to an earlier migration state.
        Useful for fixing issues or testing different schema versions.

        Examples
        --------
        uv run db downgrade -1       # Rollback one migration
        uv run db downgrade base    # Rollback to initial empty state
        uv run db downgrade abc123  # Rollback to specific revision

        ⚠️  WARNING: This can cause data loss if rolling back migrations
        that added tables/columns. Always backup first!
        """
        self.rich.print_section("⬇️ Downgrade Database", "yellow")
        self.rich.rich_print(f"[bold yellow]⚠️  Rolling back to revision: {revision}[/bold yellow]")
        self.rich.rich_print("[yellow]This may cause data loss - backup your database first![/yellow]")
        self.rich.rich_print("")

        # Require confirmation for dangerous operations
        if revision != "-1":  # Allow quick rollback without confirmation
            response = input(f"Type 'yes' to downgrade to {revision}: ")
            if response.lower() != "yes":
                self.rich.print_info("Downgrade cancelled")
                return

        try:
            self._run_command(["uv", "run", "alembic", "downgrade", revision])
            self.rich.print_success(f"Successfully downgraded to revision: {revision}")
        except subprocess.CalledProcessError:
            self.rich.print_error(f"Failed to downgrade to revision: {revision}")

    def version(self) -> None:
        """Show version information for database components.

        Displays version information for the database CLI, alembic,
        and database driver components.
        """
        self.rich.print_section("📌 Version Information", "blue")
        self.rich.rich_print("[bold blue]Showing database version information...[/bold blue]")

        try:
            self.rich.rich_print("[cyan]Current migration:[/cyan]")
            self._run_command(["uv", "run", "alembic", "current"])

            self.rich.rich_print("[cyan]Database driver:[/cyan]")
            self._run_command(
                ["uv", "run", "python", "-c", "import psycopg; print(f'psycopg version: {psycopg.__version__}')"],
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
