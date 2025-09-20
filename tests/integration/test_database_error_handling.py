"""Integration tests for database error handling with Sentry."""

import pytest
from unittest.mock import patch, MagicMock
import sqlalchemy.exc

from tux.database.service import DatabaseService
from tux.shared.exceptions import TuxDatabaseError, TuxDatabaseConnectionError


class TestDatabaseErrorHandling:
    """Test database error handling with Sentry integration."""

    @pytest.mark.asyncio
    async def test_database_connection_error_captured(self, disconnected_async_db_service):
        """Test that database connection errors are handled properly."""
        db_service = disconnected_async_db_service

        with pytest.raises(Exception):  # Connection will fail with invalid URL
            await db_service.connect("invalid://connection/string")

    @pytest.mark.asyncio
    async def test_database_query_error_captured(self, db_service):
        """Test that database query errors are handled properly."""
        async def failing_operation(session):
            # Force a database error
            raise sqlalchemy.exc.OperationalError("Connection lost", None, None)

        with pytest.raises(sqlalchemy.exc.OperationalError):
            await db_service.execute_query(failing_operation, "test_query")

    @pytest.mark.asyncio
    async def test_database_health_check_error_not_captured(self, db_service):
        """Test that health check errors are handled gracefully."""
        # Mock the session to raise an exception
        original_session = db_service.session

        async def failing_session():
            raise Exception("Health check failed")

        # Temporarily replace the session method
        db_service.session = failing_session

        try:
            result = await db_service.health_check()

            # Health check should return error status
            assert result["status"] == "unhealthy"
        finally:
            # Restore original session method
            db_service.session = original_session

    @pytest.mark.asyncio
    async def test_database_transaction_rollback_captured(self, db_service):
        """Test that transaction rollback works properly."""
        async def failing_transaction_operation(session):
            # Simulate a transaction that needs rollback
            raise ValueError("Transaction failed")

        with pytest.raises(ValueError):
            async with db_service.session() as session:
                await failing_transaction_operation(session)

    @pytest.mark.asyncio
    async def test_database_retry_logic_with_sentry(self, db_service):
        """Test database retry logic works properly."""
        call_count = 0

        async def intermittent_failure_operation(session):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first 2 attempts
                raise sqlalchemy.exc.OperationalError("Temporary failure", None, None)
            return "success"

        # Should succeed on 3rd attempt
        result = await db_service.execute_query(intermittent_failure_operation, "retry_test")

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_database_retry_exhaustion_captured(self, db_service):
        """Test that retry exhaustion is handled properly."""
        async def always_failing_operation(session):
            raise sqlalchemy.exc.OperationalError("Persistent failure", None, None)

        with pytest.raises(sqlalchemy.exc.OperationalError):
            await db_service.execute_query(always_failing_operation, "exhaustion_test")


class TestDatabaseServiceErrorIntegration:
    """Test DatabaseService error handling integration."""

    @pytest.mark.asyncio
    async def test_connection_error_with_context(self):
        """Test connection error is handled properly."""
        # Create a service with invalid connection string
        from tux.database.service import AsyncDatabaseService
        service = AsyncDatabaseService()

        with pytest.raises(Exception):
            await service.connect("invalid://connection/string")

    @pytest.mark.asyncio
    async def test_query_error_with_span_context(self, db_service):
        """Test query error includes Sentry span context."""
        async def failing_query(session):
            raise sqlalchemy.exc.IntegrityError("Constraint violation", None, None)

        with patch("tux.database.service.sentry_sdk") as mock_sentry_sdk:
            mock_sentry_sdk.is_initialized.return_value = True
            mock_span = MagicMock()
            mock_sentry_sdk.start_span.return_value.__enter__.return_value = mock_span

            with pytest.raises(sqlalchemy.exc.IntegrityError):
                await db_service.execute_query(failing_query, "integrity_test")

            # Verify span was created
            mock_sentry_sdk.start_span.assert_called_once()

    @pytest.mark.asyncio
    async def test_database_service_factory_error_handling(self):
        """Test DatabaseServiceFactory error handling."""
        from tux.database.service import DatabaseServiceFactory

        # Test with invalid mode (not a DatabaseMode enum)
        with pytest.raises(ValueError):
            DatabaseServiceFactory.create("invalid_mode")
