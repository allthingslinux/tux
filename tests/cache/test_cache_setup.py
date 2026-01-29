"""Unit tests for CacheSetupService (Valkey setup during bot init)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.cache import GuildConfigCacheManager, JailStatusCache
from tux.core.setup.cache_setup import CacheSetupService

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_bot() -> MagicMock:
    """Bot mock with cache_service attribute."""
    bot = MagicMock()
    bot.cache_service = None
    return bot


@pytest.mark.asyncio
async def test_setup_when_valkey_url_empty_sets_cache_service_none(
    mock_bot: MagicMock,
) -> None:
    """When CONFIG.valkey_url is empty, bot.cache_service is None and backend is in-memory."""
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = ""
        service = CacheSetupService(mock_bot)
        await service.setup()
    assert mock_bot.cache_service is None


@pytest.mark.asyncio
async def test_setup_when_valkey_url_none_sets_cache_service_none(
    mock_bot: MagicMock,
) -> None:
    """When CONFIG.valkey_url is None (falsy), bot.cache_service is None."""
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = None
        service = CacheSetupService(mock_bot)
        await service.setup()
    assert mock_bot.cache_service is None


@pytest.mark.asyncio
async def test_setup_when_connect_raises_sets_cache_service_none(
    mock_bot: MagicMock,
) -> None:
    """When Valkey URL is set but connect() raises, bot.cache_service is None."""
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with patch("tux.core.setup.cache_setup.CacheService") as mock_cls:
            instance = MagicMock()
            instance.connect = AsyncMock(side_effect=ConnectionError("refused"))
            instance.close = AsyncMock()
            mock_cls.return_value = instance
            service = CacheSetupService(mock_bot)
            await service.setup()
    assert mock_bot.cache_service is None
    instance.connect.assert_called_once()
    instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_setup_when_ping_fails_closes_service_and_sets_none(
    mock_bot: MagicMock,
) -> None:
    """When connect succeeds but ping() returns False, service is closed and cache_service is None."""
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with patch("tux.core.setup.cache_setup.CacheService") as mock_cls:
            instance = MagicMock()
            instance.connect = AsyncMock()
            instance.ping = AsyncMock(return_value=False)
            instance.close = AsyncMock()
            mock_cls.return_value = instance
            service = CacheSetupService(mock_bot)
            await service.setup()
    assert mock_bot.cache_service is None
    instance.close.assert_called_once()


@pytest.mark.asyncio
async def test_setup_when_connect_and_ping_succeed_sets_cache_service(
    mock_bot: MagicMock,
) -> None:
    """When connect and ping succeed, bot.cache_service is set and backend is wired."""
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with patch("tux.core.setup.cache_setup.CacheService") as mock_cls:
            instance = MagicMock()
            instance.connect = AsyncMock()
            instance.ping = AsyncMock(return_value=True)
            mock_cls.return_value = instance
            mock_backend = MagicMock()
            mock_backend.__class__.__name__ = "ValkeyBackend"
            with patch(
                "tux.core.setup.cache_setup.get_cache_backend",
                return_value=mock_backend,
            ):
                service = CacheSetupService(mock_bot)
                await service.setup()
    assert mock_bot.cache_service is instance


@pytest.mark.asyncio
async def test_setup_wires_backend_to_singletons(mock_bot: MagicMock) -> None:
    """Setup calls set_backend on GuildConfigCacheManager and JailStatusCache."""
    backend = MagicMock()
    backend.__class__.__name__ = "InMemoryBackend"
    with patch("tux.core.setup.cache_setup.CONFIG") as mock_config:
        mock_config.valkey_url = ""
        with patch(
            "tux.core.setup.cache_setup.get_cache_backend",
            return_value=backend,
        ):
            service = CacheSetupService(mock_bot)
            await service.setup()
    guild_mgr = GuildConfigCacheManager()
    jail_cache = JailStatusCache()
    assert guild_mgr._backend is backend
    assert jail_cache._backend is backend
