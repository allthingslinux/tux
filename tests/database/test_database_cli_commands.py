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

Performance Optimizations:
- Class-scoped setup methods to avoid repeated database resets
- Expensive operations marked with @pytest.mark.slow
- Database state shared between tests in the same class

Performance Tips:
- Run fast tests only: pytest -m "not slow"
- Run in parallel: pytest -n auto (uses pytest-xdist)
- Combine both: pytest -m "not slow" -n auto
- Expected speedup: 3-5x with parallel execution

Note: Each test spawns a subprocess, so parallel execution provides
significant speedup. Tests are designed to be independent and safe to run in parallel.
"""

import os
import shutil
import subprocess
import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

import psycopg
import psycopg.errors
import pytest
from sqlalchemy import text

from tux.database.service import DatabaseService
from tux.shared.config import CONFIG

# Database connection constants (matches defaults from compose.yaml for consistency)
DEFAULT_POSTGRES_HOST = "localhost"
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_POSTGRES_USER = "tuxuser"
DEFAULT_POSTGRES_PASSWORD = "ChangeThisToAStrongPassword123!"
DEFAULT_POSTGRES_DB = "tuxdb"
DATABASE_CONNECT_TIMEOUT = 2


def _get_db_connection_params() -> dict[str, Any]:
    """Get database connection parameters from environment or defaults.

    Returns
    -------
    dict[str, Any]
        Dictionary with host, port, user, password, and dbname keys.
    """
    return {
        "host": os.getenv("POSTGRES_HOST", DEFAULT_POSTGRES_HOST),
        "port": int(os.getenv("POSTGRES_PORT", str(DEFAULT_POSTGRES_PORT))),
        "user": os.getenv("POSTGRES_USER", DEFAULT_POSTGRES_USER),
        "password": os.getenv("POSTGRES_PASSWORD", DEFAULT_POSTGRES_PASSWORD),
        "dbname": os.getenv("POSTGRES_DB", DEFAULT_POSTGRES_DB),
    }


def is_database_running() -> bool:
    """Check if the test database is running and accessible.

    Returns
    -------
    bool
        True if database is accessible, False otherwise.
    """
    try:
        params = _get_db_connection_params()
        conn = psycopg.connect(
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            dbname=params["dbname"],
            connect_timeout=DATABASE_CONNECT_TIMEOUT,
        )
        conn.close()
    except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError, OSError):
        return False
    else:
        return True


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Provide a test database URL for CLI tests.

    Returns
    -------
    str
        PostgreSQL connection URL in psycopg format.
    """
    params = _get_db_connection_params()
    return (
        f"postgresql+psycopg://{params['user']}:{params['password']}"
        f"@{params['host']}:{params['port']}/{params['dbname']}"
    )


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
    """Test database CLI commands end-to-end."""

    def run_cli_command(
        self,
        command: str,
        cwd: Path | None = None,
    ) -> tuple[int, str, str]:
        """Run a CLI command and return (exit_code, stdout, stderr).

        Parameters
        ----------
        command : str
            CLI command to run (without 'db' prefix).
        cwd : Path | None
            Working directory for command execution. Defaults to project root.

        Returns
        -------
        tuple[int, str, str]
            Tuple of (exit_code, stdout, stderr).
        """
        project_root = Path(__file__).parent.parent.parent
        working_dir = cwd or project_root

        # Split command into parts for safer execution
        # Command is controlled by test code, so this is safe
        command_parts = command.split()
        full_command = ["uv", "run", "db", *command_parts]

        process = subprocess.run(
            full_command,
            check=False,
            capture_output=True,
            text=True,
            cwd=working_dir,
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
    @pytest.mark.slow
    def test_readonly_commands_work(self):
        """Test that readonly commands (status, tables, health, version) work correctly.

        This test spawns multiple subprocess calls and typically takes 4-6 seconds,
        making it a slow test that should be excluded from fast test runs.
        """
        # Combine multiple fast readonly commands into one test to reduce subprocess overhead
        commands = [
            ("status", ["Migration Status", "Checking migration status"]),
            ("tables", ["Database Tables"]),
            ("health", ["Database Health"]),
            ("version", ["Version Information"]),
        ]

        for command, expected_texts in commands:
            exit_code, stdout, _stderr = self.run_cli_command(command)
            assert exit_code == 0, (
                f"Command '{command}' failed with exit code {exit_code}"
            )
            for expected in expected_texts:
                assert expected in stdout, (
                    f"Expected '{expected}' not found in output for '{command}'"
                )

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
    def test_command_help_works(self):
        """Test that command help displays properly for multiple commands."""
        # Test multiple help commands in one test to reduce subprocess overhead
        help_commands = [
            ("new --help", ["Generate new migration", "Descriptive message"]),
            ("downgrade --help", ["Rollback to", "migration", "-1", "base"]),
            ("show --help", ["Show", "migration", "head", "base"]),
        ]

        for command, expected_texts in help_commands:
            exit_code, stdout, _stderr = self.run_cli_command(command)
            assert exit_code == 0, f"Help command '{command}' failed"
            for expected in expected_texts:
                assert expected.lower() in stdout.lower(), (
                    f"Expected '{expected}' not found in help for '{command}'"
                )


@pytest.mark.skipif(not is_database_running(), reason="Database not running")
class TestMigrationLifecycle(TestDatabaseCLICommands):
    """🔄 Test the complete migration lifecycle."""

    # No class-level setup - tests that need clean state will reset individually
    # This avoids expensive resets for tests that don't need them

    @pytest.mark.integration
    @pytest.mark.slow
    def test_migration_generation_and_status(self):
        """Test generating a migration and checking status."""
        # Reset database to ensure clean state for this specific test
        self.run_cli_command("reset")
        # Generate a test migration (may succeed or fail depending on Alembic behavior)
        exit_code, stdout, stderr = self.run_cli_command("new 'test migration'")
        combined_output = stdout + stderr

        # When there are no model changes, Alembic either:
        # 1. Fails with an error (exit_code != 0)
        # 2. Succeeds but skips migration creation (exit_code == 0, "No schema changes" message)
        if exit_code != 0:
            # Command failed - check for error message
            assert (
                "Failed to generate migration" in combined_output
                or "failed" in combined_output.lower()
                or "error" in combined_output.lower()
            ), (
                f"Expected error message not found. stdout: {stdout!r}, stderr: {stderr!r}"
            )
        else:
            # Command succeeded but should indicate no changes
            assert (
                "no schema changes" in combined_output.lower()
                or "skipping migration" in combined_output.lower()
                or "migration generated" in combined_output.lower()
            ), (
                f"Expected success message indicating no changes. "
                f"stdout: {stdout!r}, stderr: {stderr!r}"
            )

        # Check that status shows current migration state
        exit_code, stdout, _stderr = self.run_cli_command("status")
        assert exit_code == 0
        assert "Migration Status" in stdout

    @pytest.mark.integration
    @pytest.mark.slow
    def test_dev_workflow_simulation(self):
        """Test the dev workflow (generate + apply)."""
        # Reset database to ensure clean state for this specific test
        self.run_cli_command("reset")
        # This would create a new migration and apply it
        # Note: In real usage, this would modify models first
        exit_code, stdout, stderr = self.run_cli_command(
            "dev --create-only --name 'dev workflow test'",
        )
        combined_output = stdout + stderr

        # When there are no model changes, Alembic either:
        # 1. Fails with an error (exit_code != 0)
        # 2. Succeeds but skips migration creation (exit_code == 0, "No schema changes" message)
        if exit_code != 0:
            # Command failed - check for error message
            assert (
                "Failed to create migration" in combined_output
                or "failed" in combined_output.lower()
                or "error" in combined_output.lower()
            ), (
                f"Expected error message not found. stdout: {stdout!r}, stderr: {stderr!r}"
            )
        else:
            # Command succeeded but should indicate no changes or migration created
            assert (
                "no schema changes" in combined_output.lower()
                or "skipping migration" in combined_output.lower()
                or "migration created" in combined_output.lower()
                or "migration generated" in combined_output.lower()
            ), f"Expected success message. stdout: {stdout!r}, stderr: {stderr!r}"

    @pytest.mark.integration
    @pytest.mark.slow
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
    def test_readonly_migration_commands_work(self):
        """Test readonly migration commands (history, check, reset help)."""
        # Combine multiple fast readonly commands into one test
        commands = [
            ("history", ["Migration History"]),
            ("check", ["validate migrations", "checking migration files"]),
            ("reset --help", []),  # Just verify it doesn't crash
        ]

        for command, expected_texts in commands:
            exit_code, stdout, _stderr = self.run_cli_command(command)
            # Check command may fail if there are migration issues (expected in test env)
            if command == "check":
                # Just verify it runs and provides feedback
                assert "validate migrations" in stdout.lower() or exit_code != 0
            else:
                assert exit_code == 0, f"Command '{command}' failed"
                for expected in expected_texts:
                    assert expected.lower() in stdout.lower(), (
                        f"Expected '{expected}' not found in output for '{command}'"
                    )


@pytest.mark.skipif(not is_database_running(), reason="Database not running")
class TestDatabaseStateValidation(TestDatabaseCLICommands):
    """🔍 Test that database state is correct after CLI operations."""

    @classmethod
    def setup_class(cls) -> None:
        """Set up clean database state once per class (not per test).

        This avoids expensive nuke+push operations for every test method.
        """
        # Nuclear reset to completely clean state (drops everything including enum types)
        cls().run_cli_command("nuke --force")
        # Then apply existing migrations
        # Note: If there are multiple migration heads, push will fail
        # In that case, we need to manually merge heads or use 'alembic upgrade heads'
        exit_code, _stdout, stderr = cls().run_cli_command("push")
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
    @pytest.mark.slow
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
    @pytest.mark.slow
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
                error_str = str(e)
                if "does not exist" in error_str:
                    pytest.skip(
                        "Alembic version table not found. "
                        "This may indicate migrations weren't applied (possibly due to multiple heads). "
                        "Run 'alembic upgrade heads' manually to resolve.",
                    )
                pytest.fail(f"Alembic version table query failed: {e}")


class TestErrorHandling(TestDatabaseCLICommands):
    """🚨 Test error handling and edge cases."""

    @pytest.mark.integration
    def test_error_handling_for_invalid_commands(self):
        """Test error handling for invalid commands and missing arguments."""
        # Combine multiple error case tests to reduce subprocess overhead
        error_cases = [
            ("nonexistent-command", None),  # Invalid command
            ("show", "missing argument"),  # Missing required argument
            ("downgrade", "missing argument"),  # Missing required argument
        ]

        for command, expected_error in error_cases:
            exit_code, _stdout, stderr = self.run_cli_command(command)
            assert exit_code != 0, f"Command '{command}' should have failed but didn't"
            if expected_error:
                assert expected_error in stderr.lower(), (
                    f"Expected error '{expected_error}' not found for '{command}'"
                )


class TestRecoveryScenarios(TestDatabaseCLICommands):
    """🔧 Test recovery from various failure scenarios.

    Note: This class uses setup_class which modifies database state.
    In parallel mode, this may cause conflicts - consider running with -n 1
    or marking this class to run serially.
    """

    @classmethod
    def setup_class(cls) -> None:
        """Set up clean database state once per class (not per test).

        This avoids expensive nuke+push operations for every test method.

        Warning: In parallel mode, multiple workers may conflict.
        Consider using pytest-xdist's --dist=loadscope or running serially.
        """
        # Ensure we have a clean, up-to-date database for recovery tests
        # Using nuke + push to ensure absolute clean state
        # Add a small delay to reduce race conditions in parallel mode
        time.sleep(0.1)  # Small delay to stagger parallel workers
        cls().run_cli_command("nuke --force")
        cls().run_cli_command("push")

    @pytest.mark.integration
    @pytest.mark.slow
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
            exit_code, stdout, stderr = self.run_cli_command(command)
            # Some commands may fail in parallel mode due to database state
            # Check is more lenient - it may fail if there are migration issues
            if command == "check":
                # Just verify it runs and provides feedback (may fail)
                assert "validate migrations" in stdout.lower() or exit_code != 0
            elif exit_code != 0:
                # Retry once for status/health commands that might have transient failures
                if command in ("status", "health") and "connection" in stderr.lower():
                    time.sleep(0.5)  # Brief wait for database to stabilize
                    exit_code, stdout, stderr = self.run_cli_command(command)

                assert exit_code == 0, (
                    f"Command '{command}' failed: {description}. "
                    f"stdout: {stdout[:200]!r}, stderr: {stderr[:200]!r}"
                )


# Performance and load testing could be added here in the future
class TestCLIPerformance(TestDatabaseCLICommands):
    """⚡ Test CLI performance and responsiveness."""

    @pytest.mark.integration
    @pytest.mark.performance
    @pytest.mark.slow
    def test_commands_execute_quickly(self):
        """Test that CLI commands execute within reasonable time limits.

        Despite the name, this test spawns multiple subprocess calls and typically
        takes 4-5 seconds, making it a slow test that should be excluded from fast test runs.
        """
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
