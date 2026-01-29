"""Unit tests for PrefixManager (prefix resolution with cache backend)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.core.prefix_manager import PrefixManager

pytestmark = pytest.mark.unit

TEST_GUILD_ID = 123456789


@pytest.fixture
def mock_bot() -> MagicMock:
    """Bot mock with cache_service and default prefix."""
    bot = MagicMock()
    bot.cache_service = None
    return bot


@pytest.fixture
def prefix_manager(mock_bot: MagicMock) -> PrefixManager:
    """PrefixManager with mocked bot."""
    with patch("tux.core.prefix_manager.CONFIG") as mock_config:
        mock_config.get_prefix.return_value = "!"
        mock_config.is_prefix_override_enabled.return_value = False
        return PrefixManager(mock_bot)


@pytest.mark.asyncio
async def test_get_prefix_returns_from_backend_when_cached(
    prefix_manager: PrefixManager,
    mock_bot: MagicMock,
) -> None:
    """get_prefix returns value from backend when backend has it and updates _prefix_cache."""
    mock_backend = MagicMock()
    mock_backend.get = AsyncMock(return_value="?")
    with patch(
        "tux.core.prefix_manager.get_cache_backend",
        return_value=mock_backend,
    ):
        result = await prefix_manager.get_prefix(TEST_GUILD_ID)
    assert result == "?"
    assert prefix_manager._prefix_cache[TEST_GUILD_ID] == "?"


@pytest.mark.asyncio
async def test_get_prefix_returns_from_sync_cache_on_hit(
    prefix_manager: PrefixManager,
) -> None:
    """get_prefix returns from _prefix_cache when key already in cache (no backend call)."""
    prefix_manager._prefix_cache[TEST_GUILD_ID] = "."
    result = await prefix_manager.get_prefix(TEST_GUILD_ID)
    assert result == "."


@pytest.mark.asyncio
async def test_set_prefix_writes_to_backend(
    prefix_manager: PrefixManager,
    mock_bot: MagicMock,
) -> None:
    """set_prefix updates _prefix_cache and writes to backend."""
    mock_backend = MagicMock()
    mock_backend.set = AsyncMock()
    with (
        patch(
            "tux.core.prefix_manager.get_cache_backend",
            return_value=mock_backend,
        ),
        patch.object(
            prefix_manager,
            "_persist_prefix",
            new_callable=AsyncMock,
        ),
    ):
        await prefix_manager.set_prefix(TEST_GUILD_ID, "?")
    assert prefix_manager._prefix_cache[TEST_GUILD_ID] == "?"
    mock_backend.set.assert_called_once_with(
        f"prefix:{TEST_GUILD_ID}",
        "?",
        ttl_sec=None,
    )


@pytest.mark.asyncio
async def test_get_prefix_returns_default_when_guild_id_none(
    prefix_manager: PrefixManager,
) -> None:
    """get_prefix with guild_id None returns default prefix."""
    result = await prefix_manager.get_prefix(None)
    assert result == "!"
