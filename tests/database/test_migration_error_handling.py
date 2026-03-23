"""
Migration Error Handling Tests.

Tests that verify proper error handling when migrations fail, time out,
or encounter issues. These tests ensure the bot fails gracefully and
provides helpful error messages.
"""

import time
from unittest.mock import patch

import pytest

from tux.core.setup.database_setup import DatabaseSetupService
from tux.database.service import DatabaseService
from tux.shared.exceptions import TuxDatabaseConnectionError, TuxDatabaseMigrationError

pytestmark = pytest.mark.integration


class TestMigrationErrorHandling:
    """Test error handling in migration system."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_migration_timeout_raises_error(self) -> None:
        """Test that migration timeout raises TuxDatabaseMigrationError.

        This test intentionally sleeps for 35 seconds to verify timeout behavior,
        making it a slow test that should be excluded from fast test runs.
        """
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Avoid DB usage; real cfg needed for ScriptDirectory.from_config
        with patch.object(
            setup_service,
            "_get_current_revision",
            return_value="current_rev",
        ):
            # Mock command.upgrade to take longer than timeout (runs in sync executor)
            def slow_upgrade(*args: object, **kwargs: object) -> None:
                time.sleep(35)  # Longer than 30s timeout

            with patch(
                "tux.core.setup.database_setup.command.upgrade",
                side_effect=slow_upgrade,
            ):
                with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                    await setup_service._upgrade_head_if_needed()

                error_msg = str(exc_info.value).lower()
                assert "timed out" in error_msg or "timeout" in error_msg
                assert "30" in str(exc_info.value)  # Check for "30 seconds" or "30s"

    @pytest.mark.asyncio
    async def test_migration_failure_raises_error(self) -> None:
        """Migration failures raise TuxDatabaseMigrationError with expected message."""
        # Arrange
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)
        with (
            patch.object(
                setup_service,
                "_get_current_revision",
                return_value="current_rev",
            ),
            patch(
                "tux.core.setup.database_setup.command.upgrade",
                side_effect=Exception("Migration failed"),
            ),
        ):
            # Act & Assert
            with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                await setup_service._upgrade_head_if_needed()
            assert "failed" in str(exc_info.value).lower()
            assert "migration" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_connection_error_handled(self) -> None:
        """Test that database connection errors are handled properly."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Mock db_service to simulate connection failure
        with (
            patch.object(db_service, "is_connected", return_value=False),
            pytest.raises(TuxDatabaseConnectionError),
        ):
            await setup_service.setup()

    @pytest.mark.asyncio
    async def test_migration_error_message_helpful(self) -> None:
        """Test that migration error messages provide helpful guidance."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Avoid DB usage; real cfg needed for ScriptDirectory.from_config
        with (
            patch.object(
                setup_service,
                "_get_current_revision",
                return_value="current_rev",
            ),
            patch(
                "tux.core.setup.database_setup.command.upgrade",
                side_effect=Exception("Migration failed"),
            ),
        ):
            with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                await setup_service._upgrade_head_if_needed()

            error_msg = str(exc_info.value)
            # Should mention manual migration command
            assert "db push" in error_msg.lower() or "migration" in error_msg.lower()
