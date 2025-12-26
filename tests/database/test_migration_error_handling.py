"""
Migration Error Handling Tests.

Tests that verify proper error handling when migrations fail, time out,
or encounter issues. These tests ensure the bot fails gracefully and
provides helpful error messages.
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from tux.core.setup.database_setup import DatabaseSetupService
from tux.database.service import DatabaseService
from tux.shared.exceptions import TuxDatabaseConnectionError, TuxDatabaseMigrationError


class TestMigrationErrorHandling:
    """Test error handling in migration system."""

    @pytest.mark.asyncio
    async def test_migration_timeout_raises_error(self):
        """Test that migration timeout raises TuxDatabaseMigrationError."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Mock _build_alembic_config to return a config
        with patch.object(setup_service, "_build_alembic_config") as mock_config:
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            # Mock command.current to take longer than timeout
            # Note: This runs in a sync executor, so use time.sleep, not asyncio.sleep
            def slow_operation(*args, **kwargs):
                time.sleep(35)  # Longer than 30s timeout

            with patch(
                "tux.core.setup.database_setup.command.current",
                side_effect=slow_operation,
            ):
                with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                    await setup_service._upgrade_head_if_needed()

                error_msg = str(exc_info.value).lower()
                assert "timed out" in error_msg or "timeout" in error_msg
                assert "30" in str(exc_info.value)  # Check for "30 seconds" or "30s"

    @pytest.mark.asyncio
    async def test_migration_failure_raises_error(self):
        """Test that migration failures raise TuxDatabaseMigrationError."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Mock _build_alembic_config
        with patch.object(setup_service, "_build_alembic_config") as mock_config:
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            # Mock command.current to raise an error
            with patch(
                "tux.core.setup.database_setup.command.current",
                side_effect=Exception("Migration failed"),
            ):
                with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                    await setup_service._upgrade_head_if_needed()

                assert "failed" in str(exc_info.value).lower()
                assert "migration" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_database_connection_error_handled(self):
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
    async def test_migration_error_message_helpful(self):
        """Test that migration error messages provide helpful guidance."""
        db_service = DatabaseService()
        setup_service = DatabaseSetupService(db_service)

        # Mock _build_alembic_config
        with patch.object(setup_service, "_build_alembic_config") as mock_config:
            mock_cfg = MagicMock()
            mock_config.return_value = mock_cfg

            # Mock command.current to raise an error
            with patch(
                "tux.core.setup.database_setup.command.current",
                side_effect=Exception("Migration failed"),
            ):
                with pytest.raises(TuxDatabaseMigrationError) as exc_info:
                    await setup_service._upgrade_head_if_needed()

                error_msg = str(exc_info.value)
                # Should mention manual migration command
                assert (
                    "db push" in error_msg.lower() or "migration" in error_msg.lower()
                )
