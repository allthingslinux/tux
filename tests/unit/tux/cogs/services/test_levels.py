"""Unit tests for the LevelsService cog with dependency injection."""

import pytest
from unittest.mock import AsyncMock, Mock, patch

from tux.cogs.services.levels import LevelsService
from tests.fixtures.dependency_injection import mock_bot_with_container


@pytest.fixture
def levels_service_cog(mock_bot_with_container):
    """Create a LevelsService cog instance with mocked dependencies."""
    return LevelsService(mock_bot_with_container)


@pytest.mark.asyncio
class TestLevelsServiceCog:
    """Test cases for the LevelsService cog."""

    async def test_cog_initialization(self, levels_service_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert levels_service_cog.bot is not None
        assert levels_service_cog.db_service is not None
        assert hasattr(levels_service_cog, 'db')  # Backward compatibility
        assert hasattr(levels_service_cog, 'xp_cooldown')
        assert hasattr(levels_service_cog, 'levels_exponent')

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        cog = LevelsService(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, 'db')
        assert cog.db is not None

    def test_cog_representation(self, levels_service_cog):
        """Test the string representation of the cog."""
        repr_str = repr(levels_service_cog)
        assert "LevelsService" in repr_str
        assert "injection=" in repr_str
