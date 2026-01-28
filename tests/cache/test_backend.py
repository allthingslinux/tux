"""Unit tests for cache backends and get_cache_backend."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from tux.cache.backend import (
    KEY_PREFIX,
    InMemoryBackend,
    ValkeyBackend,
    get_cache_backend,
)


@pytest.mark.unit
class TestInMemoryBackend:
    """InMemoryBackend get/set/delete/exists."""

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self) -> None:
        """Get with missing key returns None."""
        backend = InMemoryBackend()
        assert await backend.get("missing") is None

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(self) -> None:
        """Set then get returns the same value."""
        backend = InMemoryBackend()
        await backend.set("k", {"a": 1})
        assert await backend.get("k") == {"a": 1}

    @pytest.mark.asyncio
    async def test_delete_removes_key(self) -> None:
        """Delete removes the key; get returns None."""
        backend = InMemoryBackend()
        await backend.set("k", 42)
        await backend.delete("k")
        assert await backend.get("k") is None

    @pytest.mark.asyncio
    async def test_exists_true_after_set_false_after_delete(self) -> None:
        """Exists is True after set, False after delete."""
        backend = InMemoryBackend()
        assert await backend.exists("k") is False
        await backend.set("k", 1)
        assert await backend.exists("k") is True
        await backend.delete("k")
        assert await backend.exists("k") is False

    @pytest.mark.asyncio
    async def test_set_accepts_ttl_sec_ignored(self) -> None:
        """InMemoryBackend accepts ttl_sec (TTLCache handles TTL internally)."""
        backend = InMemoryBackend(default_ttl=60.0)
        await backend.set("k", "v", ttl_sec=120.0)
        assert await backend.get("k") == "v"


@pytest.mark.unit
class TestValkeyBackend:
    """ValkeyBackend with mock client: prefix, JSON, setex."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Fake async Valkey client (in-memory dict, get/set/delete/exists)."""
        store: dict[str, str] = {}

        async def get(key: str) -> str | None:
            return store.get(key)

        async def set_key(key: str, value: str) -> None:
            store[key] = value

        async def setex_key(key: str, ttl_sec: int, value: str) -> None:
            store[key] = value

        async def delete(key: str) -> None:
            store.pop(key, None)

        async def exists(key: str) -> int:
            return 1 if key in store else 0

        client = MagicMock()
        client.get = AsyncMock(side_effect=get)
        client.set = AsyncMock(side_effect=set_key)
        client.setex = AsyncMock(side_effect=setex_key)
        client.delete = AsyncMock(side_effect=delete)
        client.exists = AsyncMock(side_effect=exists)
        return client

    @pytest.mark.asyncio
    async def test_key_prefix_prepended(self, mock_client: MagicMock) -> None:
        """Keys are stored with tux: prefix."""
        backend = ValkeyBackend(mock_client)
        await backend.set("foo", "bar")
        mock_client.set.assert_called_once()
        call_key = mock_client.set.call_args[0][0]
        assert call_key == f"{KEY_PREFIX}foo"

    @pytest.mark.asyncio
    async def test_key_prefix_not_doubled_when_already_prefixed(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Keys already starting with tux: are not double-prefixed."""
        backend = ValkeyBackend(mock_client)
        await backend.set("tux:already", "v")
        mock_client.set.assert_called_once()
        assert mock_client.set.call_args[0][0] == "tux:already"

    @pytest.mark.asyncio
    async def test_value_serialized_as_json(self, mock_client: MagicMock) -> None:
        """Non-string values are JSON-serialized."""
        backend = ValkeyBackend(mock_client)
        await backend.set("k", {"x": 1})
        mock_client.set.assert_called_once()
        payload = mock_client.set.call_args[0][1]
        assert payload == json.dumps({"x": 1})

    @pytest.mark.asyncio
    async def test_string_value_stored_as_is(self, mock_client: MagicMock) -> None:
        """String values are stored as-is (no extra JSON)."""
        backend = ValkeyBackend(mock_client)
        await backend.set("k", "plain")
        mock_client.set.assert_called_once()
        assert mock_client.set.call_args[0][1] == "plain"

    @pytest.mark.asyncio
    async def test_get_deserializes_json(self, mock_client: MagicMock) -> None:
        """Get returns JSON-deserialized value."""
        backend = ValkeyBackend(mock_client)
        await backend.set("k", {"a": 1})
        # Mock client stores in our side_effect dict; get reads from it
        # Our fake get returns the raw string, ValkeyBackend will json.loads it
        raw = json.dumps({"a": 1})
        mock_client.get = AsyncMock(return_value=raw)
        backend2 = ValkeyBackend(mock_client)
        result = await backend2.get("k")
        assert result == {"a": 1}

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, mock_client: MagicMock) -> None:
        """Get returns None when key is missing."""
        mock_client.get = AsyncMock(return_value=None)
        backend = ValkeyBackend(mock_client)
        assert await backend.get("missing") is None

    @pytest.mark.asyncio
    async def test_setex_called_when_ttl_sec_provided(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Set with ttl_sec uses setex."""
        backend = ValkeyBackend(mock_client)
        await backend.set("k", "v", ttl_sec=60.0)
        mock_client.setex.assert_called_once()
        args = mock_client.setex.call_args[0]
        assert args[0] == f"{KEY_PREFIX}k"
        assert args[1] == 60
        assert args[2] == "v"

    @pytest.mark.asyncio
    async def test_set_called_when_ttl_sec_none(self, mock_client: MagicMock) -> None:
        """Set with no ttl uses set."""
        backend = ValkeyBackend(mock_client)
        await backend.set("k", "v", ttl_sec=None)
        mock_client.set.assert_called_once()
        mock_client.setex.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_calls_client_delete_with_prefixed_key(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Delete uses prefixed key."""
        backend = ValkeyBackend(mock_client)
        await backend.delete("foo")
        mock_client.delete.assert_called_once_with(f"{KEY_PREFIX}foo")

    @pytest.mark.asyncio
    async def test_exists_calls_client_exists_with_prefixed_key(
        self,
        mock_client: MagicMock,
    ) -> None:
        """Exists uses prefixed key and returns bool."""
        mock_client.exists = AsyncMock(return_value=1)
        backend = ValkeyBackend(mock_client)
        assert await backend.exists("foo") is True
        mock_client.exists = AsyncMock(return_value=0)
        assert await backend.exists("bar") is False


@pytest.mark.unit
class TestGetCacheBackend:
    """get_cache_backend(bot) returns Valkey or InMemory."""

    def test_returns_in_memory_when_no_cache_service(self) -> None:
        """Bot without cache_service gets InMemoryBackend."""
        bot = MagicMock(spec=["cache_service"])
        del bot.cache_service
        backend = get_cache_backend(bot)
        assert isinstance(backend, InMemoryBackend)

    def test_returns_in_memory_when_cache_service_is_none(self) -> None:
        """Bot with cache_service=None gets InMemoryBackend."""
        bot = MagicMock()
        bot.cache_service = None
        backend = get_cache_backend(bot)
        assert isinstance(backend, InMemoryBackend)

    def test_fallback_backend_reused_when_valkey_unavailable(self) -> None:
        """Multiple calls with no Valkey return the same InMemoryBackend instance."""
        bot = MagicMock()
        bot.cache_service = None
        backend1 = get_cache_backend(bot)
        backend2 = get_cache_backend(bot)
        assert backend1 is backend2
        assert isinstance(backend1, InMemoryBackend)

    def test_returns_in_memory_when_not_connected(self) -> None:
        """Bot with cache_service not connected gets InMemoryBackend."""
        bot = MagicMock()
        bot.cache_service = MagicMock()
        bot.cache_service.is_connected.return_value = False
        backend = get_cache_backend(bot)
        assert isinstance(backend, InMemoryBackend)

    def test_returns_in_memory_when_client_is_none(self) -> None:
        """Bot with cache_service connected but get_client() None gets InMemoryBackend."""
        bot = MagicMock()
        bot.cache_service = MagicMock()
        bot.cache_service.is_connected.return_value = True
        bot.cache_service.get_client.return_value = None
        backend = get_cache_backend(bot)
        assert isinstance(backend, InMemoryBackend)

    def test_returns_valkey_backend_when_connected_with_client(self) -> None:
        """Bot with cache_service connected and client returns ValkeyBackend."""
        bot = MagicMock()
        client = MagicMock()
        bot.cache_service = MagicMock()
        bot.cache_service.is_connected.return_value = True
        bot.cache_service.get_client.return_value = client
        backend = get_cache_backend(bot)
        assert isinstance(backend, ValkeyBackend)
        assert backend._client is client
