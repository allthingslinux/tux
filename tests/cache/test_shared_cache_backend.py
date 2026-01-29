"""Unit tests for GuildConfigCacheManager and JailStatusCache with backend set."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from tux.cache import GuildConfigCacheManager, JailStatusCache
from tux.cache.backend import InMemoryBackend


@pytest.mark.unit
class TestGuildConfigCacheManagerWithBackend:
    """GuildConfigCacheManager get/set/invalidate when backend is set."""

    @pytest.fixture
    def backend(self) -> InMemoryBackend:
        """Fresh in-memory backend per test."""
        return InMemoryBackend()

    @pytest.fixture
    def manager(self, backend: InMemoryBackend) -> GuildConfigCacheManager:
        """Singleton with backend set."""
        manager = GuildConfigCacheManager()
        manager.set_backend(backend)
        return manager

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_cached(
        self,
        manager: GuildConfigCacheManager,
    ) -> None:
        """Get with uncached guild returns None."""
        assert await manager.get(999) is None

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(
        self,
        manager: GuildConfigCacheManager,
    ) -> None:
        """Set then get returns the same config."""
        guild_id = 12345
        await manager.set(
            guild_id,
            audit_log_id=111,
            mod_log_id=222,
            jail_role_id=333,
            jail_channel_id=444,
        )
        out = await manager.get(guild_id)
        assert out is not None
        assert out["audit_log_id"] == 111
        assert out["mod_log_id"] == 222
        assert out["jail_role_id"] == 333
        assert out["jail_channel_id"] == 444

    @pytest.mark.asyncio
    async def test_set_partial_merge(self, manager: GuildConfigCacheManager) -> None:
        """Set with partial fields merges with existing."""
        guild_id = 100
        await manager.set(guild_id, audit_log_id=1, mod_log_id=2)
        await manager.set(guild_id, jail_role_id=3)
        out = await manager.get(guild_id)
        assert out is not None
        assert out["audit_log_id"] == 1
        assert out["mod_log_id"] == 2
        assert out["jail_role_id"] == 3

    @pytest.mark.asyncio
    async def test_invalidate_removes_entry(
        self,
        manager: GuildConfigCacheManager,
    ) -> None:
        """Invalidate removes the guild config; get returns None."""
        guild_id = 200
        await manager.set(guild_id, audit_log_id=1)
        await manager.invalidate(guild_id)
        assert await manager.get(guild_id) is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_backend_returns_non_dict(
        self,
        manager: GuildConfigCacheManager,
        backend: InMemoryBackend,
    ) -> None:
        """Get when backend returns non-dict (e.g. string) returns None."""
        backend.get = AsyncMock(return_value="not-a-dict")
        guild_id = 99
        result = await manager.get(guild_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_async_set_with_backend_merges_and_writes(
        self,
        manager: GuildConfigCacheManager,
    ) -> None:
        """async_set with backend merges existing and writes to backend."""
        guild_id = 50
        await manager.async_set(guild_id, audit_log_id=10, mod_log_id=20)
        out = await manager.get(guild_id)
        assert out is not None
        assert out["audit_log_id"] == 10
        assert out["mod_log_id"] == 20

    @pytest.mark.asyncio
    async def test_clear_all_clears_in_memory_cache(
        self,
        manager: GuildConfigCacheManager,
    ) -> None:
        """clear_all clears in-memory _cache (when backend is None, get then returns None)."""
        manager._backend = None  # Use in-memory path only
        guild_id = 60
        await manager.set(guild_id, audit_log_id=1)
        await manager.clear_all()
        assert await manager.get(guild_id) is None


@pytest.mark.unit
class TestJailStatusCacheWithBackend:
    """JailStatusCache get/set/invalidate when backend is set."""

    @pytest.fixture
    def backend(self) -> InMemoryBackend:
        """Fresh in-memory backend per test."""
        return InMemoryBackend()

    @pytest.fixture
    def cache(self, backend: InMemoryBackend) -> JailStatusCache:
        """Singleton with backend set."""
        jail_cache = JailStatusCache()
        jail_cache.set_backend(backend)
        return jail_cache

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_cached(
        self,
        cache: JailStatusCache,
    ) -> None:
        """Get with uncached (guild, user) returns None."""
        assert await cache.get(1, 2) is None

    @pytest.mark.asyncio
    async def test_set_and_get_roundtrip(self, cache: JailStatusCache) -> None:
        """Set then get returns the same jail status."""
        await cache.set(10, 20, is_jailed=True)
        assert await cache.get(10, 20) is True
        await cache.set(10, 21, is_jailed=False)
        assert await cache.get(10, 21) is False

    @pytest.mark.asyncio
    async def test_invalidate_removes_entry(self, cache: JailStatusCache) -> None:
        """Invalidate removes the entry; get returns None."""
        await cache.set(5, 6, is_jailed=True)
        await cache.invalidate(5, 6)
        assert await cache.get(5, 6) is None

    @pytest.mark.asyncio
    async def test_get_or_fetch_uses_backend(self, cache: JailStatusCache) -> None:
        """get_or_fetch caches via backend and returns fetched value."""

        async def fetch() -> bool:
            return True

        result = await cache.get_or_fetch(7, 8, fetch)
        assert result is True
        assert await cache.get(7, 8) is True

    @pytest.mark.asyncio
    async def test_get_returns_bool_when_backend_returns_string(
        self,
        cache: JailStatusCache,
        backend: InMemoryBackend,
    ) -> None:
        """Get when backend returns string 'true' or '1' is normalized to bool."""
        backend.get = AsyncMock(return_value="true")
        assert await cache.get(1, 2) is True
        backend.get = AsyncMock(return_value="1")
        assert await cache.get(1, 3) is True
        backend.get = AsyncMock(return_value="false")
        assert await cache.get(1, 4) is False

    @pytest.mark.asyncio
    async def test_async_set_overwrites_when_backend_has_value(
        self,
        cache: JailStatusCache,
        backend: InMemoryBackend,
    ) -> None:
        """async_set overwrites existing value (same as set)."""
        backend.get = AsyncMock(return_value=True)
        backend.set = AsyncMock()
        await cache.async_set(10, 20, is_jailed=False)
        backend.set.assert_called_once()
        call_args = backend.set.call_args
        assert call_args[0][1] is False  # is_jailed

    @pytest.mark.asyncio
    async def test_async_set_writes_when_backend_missing(
        self,
        cache: JailStatusCache,
        backend: InMemoryBackend,
    ) -> None:
        """async_set when backend has no value writes."""
        await cache.async_set(11, 22, is_jailed=True)
        assert await cache.get(11, 22) is True

    @pytest.mark.asyncio
    async def test_invalidate_guild_removes_matching_keys(
        self,
        cache: JailStatusCache,
    ) -> None:
        """invalidate_guild removes in-memory entries for that guild (in-memory only)."""
        cache._backend = None  # Use in-memory path so _cache is populated
        await cache.set(100, 1, True)
        await cache.set(100, 2, False)
        await cache.set(101, 1, True)
        await cache.invalidate_guild(100)
        assert await cache.get(100, 1) is None
        assert await cache.get(100, 2) is None
        assert await cache.get(101, 1) is True

    @pytest.mark.asyncio
    async def test_clear_all_clears_entries(self, cache: JailStatusCache) -> None:
        """clear_all clears in-memory cache (when backend is None, get then returns None)."""
        cache._backend = None
        await cache.set(5, 6, is_jailed=True)
        await cache.clear_all()
        assert await cache.get(5, 6) is None
