"""Unit tests for GuildConfigCacheManager and JailStatusCache with backend set."""

from __future__ import annotations

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
