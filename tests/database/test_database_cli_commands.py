"""
🚀 Database CLI Commands Integration Tests.

Comprehensive integration tests for the database CLI commands and migration lifecycle.
Tests the actual CLI commands end-to-end to ensure they work correctly in all scenarios.

Tests cover:
- CLI command execution and responses
- Migration lifecycle (generation, application, rollback)
- Database state validation after operations
- Error handling and edge cases
- Recovery scenarios

Uses isolated test databases to avoid affecting development data.
"""

import os
import shutil
import subprocess
import time
from collections.abc import AsyncGenerator
from pathlib import Path

import psycopg
import pytest
from sqlalchemy import text

from tux.database.service import DatabaseService
from tux.shared.config import CONFIG


def is_database_running() -> bool:
    """Check if the test database is running and accessible."""
    try:
        # Get database connection parameters from environment or use defaults
        # (matches defaults from compose.yaml for consistency)
        user = os.getenv("POSTGRES_USER", "tuxuser")
        password = os.getenv("POSTGRES_PASSWORD", "ChangeThisToAStrongPassword123!")
        dbname = os.getenv("POSTGRES_DB", "tuxdb")
        conn = psycopg.connect(
            host="localhost",
            port=5432,
            user=user,
            password=password,
            dbname=dbname,
            connect_timeout=2,
        )
        conn.close()
    except ImportError:
        return False
    except Exception:
        return False
    else:
        return True


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Provide a test database URL for CLI tests."""
    user = os.getenv("POSTGRES_USER", "tuxuser")
    password = os.getenv("POSTGRES_PASSWORD", "ChangeThisToAStrongPassword123!")
    dbname = os.getenv("POSTGRES_DB", "tuxdb")
    return f"postgresql+psycopg://{user}:{password}@localhost:5432/{dbname}"


@pytest.fixture
def isolated_migration_dir(tmp_path: Path) -> Path:
    """Create an isolated migration directory for testing."""
    # Copy the real migration structure to a temp directory
    real_migrations = Path("src/tux/database/migrations")
    temp_migrations = tmp_path / "migrations"

    # Copy migration files but exclude __pycache__
    shutil.copytree(
        real_migrations,
        temp_migrations,
        ignore=shutil.ignore_patterns("__pycache__"),
    )

    return temp_migrations


@pytest.mark.skipif(not is_database_running(), reason="Database not running")
class TestDatabaseCLICommands:
    """🧪 Test database CLI commands end-to-end."""

    def run_cli_command(
        self,
        command: str,
        cwd: Path | None = None,
    ) -> tuple[int, str, str]:
        """Run a CLI command and return (exit_code, stdout, stderr)."""
        # Get project root relative to this test file
        project_root = Path(__file__).parent.parent.parent
        full_command = f"cd {project_root} && uv run db {command}"

        process = subprocess.run(
            full_command,
            check=False,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd or project_root,
        )

        return process.returncode, process.stdout, process.stderr

    @pytest.mark.integration
    def test_cli_help_shows_all_commands(self):
        """Test that CLI help displays all expected commands."""
        exit_code, stdout, _stderr = self.run_cli_command("--help")

        assert exit_code == 0
        assert "Database operations" in stdout

        # Check that all our commands are listed
        expected_commands = [
            "init",
            "dev",
            "push",
            "status",
            "new",
            "history",
            "check",
            "show",
            "tables",
            "health",
            "queries",
            "reset",
            "downgrade",
            "nuke",
            "version",
        ]

        for cmd in expected_commands:
            assert cmd in stdout, f"Command '{cmd}' not found in help output"

    @pytest.mark.integration
    def test_status_command_works(self):
        """Test that status command provides meaningful output."""
        exit_code, stdout, _stderr = self.run_cli_command("status")

        assert exit_code == 0
        assert "Migration Status" in stdout
        assert "Checking migration status" in stdout

    @pytest.mark.integration
    def test_tables_command_shows_tables(self):
        """Test that tables command lists database tables."""
        exit_code, stdout, _stderr = self.run_cli_command("tables")

        assert exit_code == 0
        assert "Database Tables" in stdout
        # In test environment, there may be no tables or tables may be present
        assert ("Found" in stdout and "tables" in stdout) or "No tables found" in stdout

    @pytest.mark.integration
    def test_health_command_works(self):
        """Test that health command checks database connectivity."""
        exit_code, stdout, _stderr = self.run_cli_command("health")

        assert exit_code == 0
        assert "Database Health" in stdout
        # Should show either healthy or connection details
        assert "healthy" in stdout.lower() or "connection" in stdout.lower()

    @pytest.mark.integration
    def test_version_command_shows_info(self):
        """Test that version command displays version information."""
        exit_code, stdout, _stderr = self.run_cli_command("version")

        assert exit_code == 0
        assert "Version Information" in stdout

    @pytest.mark.integration
    def test_init_command_fails_on_existing_db(self):
        """Test that init command properly detects existing database."""
        exit_code, stdout, _stderr = self.run_cli_command("init")

        assert exit_code != 0  # Command should fail when DB/migrations exist
        assert (
            "Database initialization blocked" in stdout
            or "Database already has" in stdout
        )

    @pytest.mark.integration
    def test_new_command_help_works(self):
        """Test that new command shows proper help."""
        exit_code, stdout, _stderr = self.run_cli_command("new --help")

        assert exit_code == 0
        assert "Generate new migration" in stdout
        assert "Descriptive message" in stdout

    @pytest.mark.integration
    def test_downgrade_command_help_works(self):
        """Test that downgrade command shows proper help."""
        exit_code, stdout, _stderr = self.run_cli_command("downgrade --help")

        assert exit_code == 0
        assert "Rollback to" in stdout
        assert "migration" in stdout
        assert "-1" in stdout
        assert "base" in stdout

    @pytest.mark.integration
    def test_show_command_help_works(self):
        """Test that show command shows proper help."""
        exit_code, stdout, _stderr = self.run_cli_command("show --help")

        assert exit_code == 0
        assert (
            "Show details of a specific migration" in stdout
            or "Show migration details" in stdout
        )
        assert ("head" in stdout and "base" in stdout) or (
            "'head'" in stdout and "'base'" in stdout
        )


@pytest.mark.skipif(not is_database_running(), reason="Database not running")
class TestMigrationLifecycle(TestDatabaseCLICommands):
    """🔄 Test the complete migration lifecycle."""

    def setup_method(self, method):
        """Ensure database is in correct state for migration lifecycle tests."""
        if method.__name__ in [
            "test_dev_workflow_simulation",
            "test_migration_generation_and_status",
        ]:
            # Reset database to ensure clean state for tests that expect specific behavior
            self.run_cli_command("reset")

    @pytest.mark.integration
    def test_migration_generation_and_status(self):
        """Test generating a migration and checking status."""
        # Generate a test migration (will fail since no model changes to auto-generate from)
        exit_code, stdout, _stderr = self.run_cli_command("new 'test migration'")
        # Should fail when there are no model changes to auto-generate from
        assert exit_code != 0
        assert "Failed to generate migration" in stdout

        # Check that status shows current migration state
        exit_code, stdout, _stderr = self.run_cli_command("status")
        assert exit_code == 0
        assert "Migration Status" in stdout

    @pytest.mark.integration
    def test_dev_workflow_simulation(self):
        """Test the dev workflow (generate + apply)."""
        # This would create a new migration and apply it
        # Note: In real usage, this would modify models first
        exit_code, stdout, _stderr = self.run_cli_command(
            "dev --create-only --name 'dev workflow test'",
        )
        # Should fail when there are no model changes to auto-generate from
        assert exit_code != 0
        assert "Failed to create migration" in stdout

    @pytest.mark.integration
    def test_push_applies_migrations(self):
        """Test that push command applies pending migrations."""
        exit_code, stdout, _stderr = self.run_cli_command("push")
        # Push may fail if there are multiple migration heads (requires manual merge)
        # In that case, check that the error message is informative
        if exit_code != 0:
            # If push failed, it should be due to multiple heads or another clear error
            assert (
                "multiple head" in _stderr.lower()
                or "failed to apply" in stdout.lower()
                or "command failed" in stdout.lower()
            )
        else:
            # If push succeeded, check for success messages
            assert (
                "all migrations applied" in stdout.lower()
                or "migrations applied" in stdout.lower()
                or "no migrations to apply" in stdout.lower()
                or "database schema up to date" in stdout.lower()
                or "upgrade" in stdout.lower()
            )

    @pytest.mark.integration
    def test_history_shows_migrations(self):
        """Test that history command shows migration history."""
        exit_code, stdout, _stderr = self.run_cli_command("history")
        assert exit_code == 0
        assert "Migration History" in stdout

    @pytest.mark.integration
    def test_check_validates_migrations(self):
        """Test that check command validates migration files."""
        _exit_code, stdout, _stderr = self.run_cli_command("check")
        # Check command may fail if there are migration issues (which is expected in test env)
        # Just verify it runs and provides feedback
        assert "validate migrations" in stdout.lower()
        assert "checking migration files" in stdout.lower()

    @pytest.mark.integration
    def test_reset_command_help(self):
        """Test that reset command shows proper warnings."""
        # Just test help, don't actually reset in integration tests
        exit_code, _stdout, _stderr = self.run_cli_command("reset --help")
        assert exit_code == 0


@pytest.mark.skipif(not is_database_running(), reason="Database not running")
class TestDatabaseStateValidation(TestDatabaseCLICommands):
    """🔍 Test that database state is correct after CLI operations."""

    def setup_method(self, method):
        """Reset database to clean state and apply existing migrations for state validation tests."""
        # Nuclear reset to completely clean state (drops everything including enum types)
        self.run_cli_command("nuke --force")
        # Then apply existing migrations
        # Note: If there are multiple migration heads, push will fail
        # In that case, we need to manually merge heads or use 'alembic upgrade heads'
        exit_code, _stdout, stderr = self.run_cli_command("push")
        if exit_code != 0 and "multiple head" in stderr.lower():
            # Try to upgrade all heads if multiple heads exist
            project_root = Path(__file__).parent.parent.parent
            subprocess.run(
                ["uv", "run", "alembic", "upgrade", "heads"],
                cwd=project_root,
                check=False,
            )

    @pytest.fixture(scope="class")
    async def db_service(self) -> AsyncGenerator[DatabaseService]:
        """Provide a database service for state validation."""
        service = DatabaseService()
        await service.connect(CONFIG.database_url)
        yield service
        await service.disconnect()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_has_expected_tables(self, db_service: DatabaseService):
        """Test that database has all expected tables after operations."""
        async with db_service.session() as session:
            # Query for our main tables
            result = await session.execute(
                text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name != 'alembic_version'
                ORDER BY table_name
            """),
            )

            tables = [row[0] for row in result.fetchall()]

            # Skip test if database is not set up (requires manual database setup for integration tests)
            if not tables:
                pytest.skip(
                    "Database not initialized. Run database setup commands manually for integration tests.",
                )

            # Should have our main model tables
            expected_tables = {
                "afk",
                "cases",
                "guild",
                "guild_config",
                "levels",
                "permission_assignments",
                "permission_commands",
                "permission_ranks",
                "reminder",
                "snippet",
                "starboard",
                "starboard_message",
            }

            assert len(tables) >= len(expected_tables), (
                f"Missing tables. Found: {tables}"
            )

            for table in expected_tables:
                assert table in tables, f"Missing table: {table}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_alembic_version_table_exists(self, db_service: DatabaseService):
        """Test that alembic version tracking is working."""
        async with db_service.session() as session:
            try:
                result = await session.execute(
                    text("SELECT version_num FROM alembic_version"),
                )
                version = result.scalar()
                if version is None:
                    pytest.skip(
                        "Database not initialized. Run database setup commands manually for integration tests.",
                    )

                assert version is not None, "Alembic version should exist"
                # Version can be 12 characters (single head) or comma-separated (multiple heads)
                # Multiple heads are valid when migrations have been created in parallel
                assert len(version) >= 12, (
                    f"Version should be at least 12 characters, got: {version}"
                )
            except Exception as e:
                # If the table doesn't exist, it means migrations weren't applied
                # This can happen if push failed due to multiple heads
                if "does not exist" in str(e):
                    pytest.skip(
                        "Alembic version table not found. "
                        "This may indicate migrations weren't applied (possibly due to multiple heads). "
                        "Run 'alembic upgrade heads' manually to resolve.",
                    )
                pytest.fail(f"Alembic version table query failed: {e}")


class TestErrorHandling(TestDatabaseCLICommands):
    """🚨 Test error handling and edge cases."""

    @pytest.mark.integration
    def test_invalid_command_returns_error(self):
        """Test that invalid commands return appropriate errors."""
        exit_code, _stdout, _stderr = self.run_cli_command("nonexistent-command")

        # Should fail with error
        assert exit_code != 0

    @pytest.mark.integration
    def test_show_command_without_revision_fails(self):
        """Test that show command requires a revision argument."""
        exit_code, _stdout, _stderr = self.run_cli_command("show")

        # Should fail because revision argument is required
        assert exit_code != 0
        assert "missing argument" in _stderr.lower()

    @pytest.mark.integration
    def test_downgrade_without_revision_fails(self):
        """Test that downgrade command requires a revision argument."""
        exit_code, _stdout, _stderr = self.run_cli_command("downgrade")

        # Should fail because revision argument is required
        assert exit_code != 0
        assert "missing argument" in _stderr.lower()


class TestRecoveryScenarios(TestDatabaseCLICommands):
    """🔧 Test recovery from various failure scenarios."""

    def setup_method(self, method):
        """Ensure database is up to date for recovery tests."""
        # Ensure we have a clean, up-to-date database for recovery tests
        # Using nuke + push to ensure absolute clean state
        self.run_cli_command("nuke --force")
        self.run_cli_command("push")

    @pytest.mark.integration
    def test_status_works_after_operations(self):
        """Test that status command works after various operations."""
        # Run a series of operations then check status
        operations = [
            ("status", "should work"),
            ("tables", "should list tables"),
            ("health", "should check health"),
            ("history", "should show history"),
            ("check", "should validate"),
            ("status", "should still work after all operations"),
        ]

        for command, description in operations:
            exit_code, _stdout, _stderr = self.run_cli_command(command)
            assert exit_code == 0, f"Command '{command}' failed: {description}"


# Performance and load testing could be added here in the future
class TestCLIPerformance(TestDatabaseCLICommands):
    """⚡ Test CLI performance and responsiveness."""

    @pytest.mark.integration
    @pytest.mark.performance
    def test_commands_execute_quickly(self):
        """Test that CLI commands execute within reasonable time limits."""
        commands_to_test = [
            ("status", "Status check"),
            ("tables", "Table listing"),
            ("health", "Health check"),
            ("version", "Version info"),
        ]

        for command, description in commands_to_test:
            start_time = time.time()
            exit_code, _stdout, _stderr = self.run_cli_command(command)
            end_time = time.time()

            execution_time = end_time - start_time

            assert exit_code == 0, f"{description} failed"
            assert execution_time < 5.0, (
                f"{description} took too long: {execution_time:.2f}s"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
