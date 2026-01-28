"""Unit tests for CacheService (connect, ping, close) with mocks."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tux.cache.service import CacheService


@pytest.mark.unit
class TestCacheService:
    """CacheService connect, is_connected, get_client, ping, close."""

    def test_is_connected_false_before_connect(self) -> None:
        """Before connect, is_connected is False."""
        service = CacheService()
        assert service.is_connected() is False

    def test_get_client_none_before_connect(self) -> None:
        """Before connect, get_client returns None."""
        service = CacheService()
        assert service.get_client() is None

    @pytest.mark.asyncio
    async def test_connect_with_empty_url_does_nothing(self) -> None:
        """Connect with no URL (CONFIG.valkey_url empty) does not set client."""
        service = CacheService()
        with patch("tux.cache.service.CONFIG") as mock_config:
            mock_config.valkey_url = None
            await service.connect()
            mock_config.valkey_url = ""
            await service.connect(url="")
        assert service._client is None
        assert service.is_connected() is False

    @pytest.mark.asyncio
    async def test_connect_with_url_sets_client(self) -> None:
        """Connect with URL sets client and is_connected True."""
        service = CacheService()
        fake_client = MagicMock()
        with patch("tux.cache.service.Valkey") as mock_valkey:
            mock_valkey.from_url.return_value = fake_client
            await service.connect(url="valkey://localhost:6379/0")
        assert service._client is fake_client
        assert service.is_connected() is True
        assert service.get_client() is fake_client

    @pytest.mark.asyncio
    async def test_connect_uses_config_valkey_url_when_url_none(self) -> None:
        """Connect with url=None uses CONFIG.valkey_url."""
        service = CacheService()
        fake_client = MagicMock()
        with patch("tux.cache.service.CONFIG") as mock_config:
            mock_config.valkey_url = "valkey://config:6379/0"
            with patch("tux.cache.service.Valkey") as mock_valkey:
                mock_valkey.from_url.return_value = fake_client
                await service.connect()
        mock_valkey.from_url.assert_called_once()
        assert mock_valkey.from_url.call_args[0][0] == "valkey://config:6379/0"

    @pytest.mark.asyncio
    async def test_ping_returns_false_when_not_connected(self) -> None:
        """Ping when not connected returns False."""
        service = CacheService()
        assert await service.ping() is False

    @pytest.mark.asyncio
    async def test_ping_returns_true_when_connected_and_ping_ok(self) -> None:
        """Ping when connected and client.ping() succeeds returns True."""
        service = CacheService()
        fake_client = MagicMock()
        fake_client.ping = AsyncMock(return_value=True)
        service._client = fake_client
        assert await service.ping() is True
        fake_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_returns_false_when_client_ping_raises(self) -> None:
        """Ping when client.ping() raises returns False."""
        service = CacheService()
        fake_client = MagicMock()
        fake_client.ping = AsyncMock(side_effect=ConnectionError("closed"))
        service._client = fake_client
        assert await service.ping() is False

    @pytest.mark.asyncio
    async def test_close_when_not_connected_is_safe(self) -> None:
        """Close when not connected does nothing."""
        service = CacheService()
        await service.close()
        assert service._client is None

    @pytest.mark.asyncio
    async def test_close_acloses_client_and_clears(self) -> None:
        """Close calls aclose on client and sets _client to None."""
        service = CacheService()
        fake_client = MagicMock()
        fake_client.aclose = AsyncMock()
        service._client = fake_client
        await service.close()
        fake_client.aclose.assert_called_once()
        assert service._client is None

    @pytest.mark.asyncio
    async def test_connect_raises_on_failure_and_clears_client(self) -> None:
        """Connect that raises leaves _client None."""
        service = CacheService()
        with patch("tux.cache.service.Valkey") as mock_valkey:
            mock_valkey.from_url.side_effect = OSError("Connection refused")
            with pytest.raises(OSError, match="Connection refused"):
                await service.connect(url="valkey://localhost:6379/0")
        assert service._client is None
