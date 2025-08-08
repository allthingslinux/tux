"""Unit tests for the AFK cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, UTC, timedelta

from tux.modules.utility.afk import Afk
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def afk_cog(mock_bot_with_container):
    """Create an AFK cog instance with mocked dependencies."""
    with patch('tux.modules.utility.afk.generate_usage'):
        with patch.object(Afk, 'handle_afk_expiration') as mock_task:
            # Mock the task to prevent it from starting
            mock_task.start = Mock()
            mock_task.is_running = Mock(return_value=False)
            cog = Afk(mock_bot_with_container)
    return cog


@pytest.mark.asyncio
class TestAfkCog:
    """Test cases for the AFK cog."""

    async def test_cog_initialization(self, afk_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert afk_cog.bot is not None
        assert afk_cog.db_service is not None
        assert hasattr(afk_cog, 'db')  # Backward compatibility

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch('tux.modules.utility.afk.generate_usage'):
            with patch.object(Afk, 'handle_afk_expiration') as mock_task:
                mock_task.start = Mock()
                mock_task.is_running = Mock(return_value=False)
                cog = Afk(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, afk_cog):
        """Test the string representation of the cog."""
        repr_str = repr(afk_cog)
        assert "Afk" in repr_str
        assert "injection=" in repr_str
