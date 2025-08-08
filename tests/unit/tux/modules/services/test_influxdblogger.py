"""Unit tests for the InfluxLogger cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.modules.services.influxdblogger import InfluxLogger
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def influx_logger_cog(mock_bot_with_container):
    """Create an InfluxLogger cog instance with mocked dependencies."""
    with patch.object(InfluxLogger, 'init_influx', return_value=False):
        with patch.object(InfluxLogger, 'logger') as mock_logger_task:
            # Mock the task to prevent it from starting
            mock_logger_task.start = Mock()
            mock_logger_task.is_running = Mock(return_value=False)
            return InfluxLogger(mock_bot_with_container)


@pytest.mark.asyncio
class TestInfluxLoggerCog:
    """Test cases for the InfluxLogger cog."""

    async def test_cog_initialization(self, influx_logger_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert influx_logger_cog.bot is not None
        assert influx_logger_cog.db_service is not None
        assert hasattr(influx_logger_cog, 'db')  # Backward compatibility
        assert influx_logger_cog.influx_write_api is None  # Not initialized in test

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch.object(InfluxLogger, 'init_influx', return_value=False):
            with patch.object(InfluxLogger, 'logger') as mock_logger_task:
                mock_logger_task.start = Mock()

                cog = InfluxLogger(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, influx_logger_cog):
        """Test the string representation of the cog."""
        repr_str = repr(influx_logger_cog)
        assert "InfluxLogger" in repr_str
        assert "injection=" in repr_str
