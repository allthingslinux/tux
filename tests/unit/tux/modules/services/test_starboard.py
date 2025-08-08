"""Unit tests for the Starboard cog with dependency injection."""

from unittest.mock import Mock, patch

import pytest

from tux.modules.services.starboard import Starboard


@pytest.fixture
def starboard_cog(mock_bot_with_container):
    """Create a Starboard cog instance with mocked dependencies."""
    with patch("tux.modules.services.starboard.generate_usage"):
        return Starboard(mock_bot_with_container)


@pytest.mark.asyncio
class TestStarboardCog:
    """Test cases for the Starboard cog."""

    async def test_cog_initialization(self, starboard_cog):
        """Test that the cog initializes correctly with dependency injection."""
        assert starboard_cog.bot is not None
        assert starboard_cog.db_service is not None
        assert hasattr(starboard_cog, "db")  # Backward compatibility

    async def test_database_service_fallback(self, mock_bot_with_container):
        """Test that the cog falls back to direct database access when service is unavailable."""
        # Remove database service from container
        mock_bot_with_container.container.get_optional = Mock(return_value=None)

        with patch("tux.modules.services.starboard.generate_usage"):
            cog = Starboard(mock_bot_with_container)

        # Should still have database access through fallback
        assert hasattr(cog, "db")
        assert cog.db is not None

    def test_cog_representation(self, starboard_cog):
        """Test the string representation of the cog."""
        repr_str = repr(starboard_cog)
        assert "Starboard" in repr_str
        assert "injection=" in repr_str
