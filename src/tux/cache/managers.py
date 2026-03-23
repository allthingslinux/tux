"""Cache managers for guild config and jail status (in-memory or backend)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from typing import Any, cast

from loguru import logger

from tux.cache.backend import AsyncCacheBackend
from tux.cache.ttl import TTLCache

# Sentinel value to indicate a field was not provided
_MISSING: Any = object()

# Setup-once, rarely change; invalidated on config update. 2h = session-friendly, low staleness risk.
GUILD_CONFIG_TTL_SEC = 7200.0  # 2 hours
# Invalidated on jail/unjail; TTL only for cold expiry.
JAIL_STATUS_TTL_SEC = 3600.0  # 1 hour

__all__ = ["GuildConfigCacheManager", "JailStatusCache"]


class GuildConfigCacheManager:
    """
    Shared cache manager for guild configuration data.

    Provides a singleton instance that can be used across the application
    to cache and invalidate guild configuration data, ensuring consistency
    when config is updated from multiple sources. Supports optional
    AsyncCacheBackend (e.g. Valkey); when set, get/set/invalidate
    are async and use the backend.
    """

    __slots__ = ("_backend", "_cache", "_locks", "_locks_lock")
    _instance: GuildConfigCacheManager | None = None
    _cache: TTLCache
    _locks: dict[int, asyncio.Lock]
    _locks_lock: asyncio.Lock
    _backend: AsyncCacheBackend | None

    def __new__(cls) -> GuildConfigCacheManager:
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = TTLCache(ttl=GUILD_CONFIG_TTL_SEC, max_size=1000)
            cls._instance._locks = {}
            cls._instance._locks_lock = asyncio.Lock()
            cls._instance._backend = None
        return cls._instance

    def set_backend(self, backend: AsyncCacheBackend) -> None:
        """Set the cache backend.

        Parameters
        ----------
        backend : AsyncCacheBackend
            Backend instance to use for cache operations.
        """
        self._backend = backend
        logger.debug(
            "GuildConfigCacheManager backend set to {}",
            type(backend).__name__,
        )

    async def _get_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific guild (thread-safe)."""
        async with self._locks_lock:
            if guild_id not in self._locks:
                self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    def _cache_key(self, guild_id: int) -> str:
        """Return the cache key for a guild (backend adds tux: prefix)."""
        return f"guild_config:{guild_id}"

    async def get(self, guild_id: int) -> dict[str, int | None] | None:
        """
        Get cached guild config for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID.

        Returns
        -------
        dict[str, int | None] | None
            Cached config dict with audit_log_id, mod_log_id, jail_role_id,
            and jail_channel_id, or None if not cached.
        """
        key = self._cache_key(guild_id)
        if self._backend is not None:
            value = await self._backend.get(key)
            return (
                cast(dict[str, int | None], value) if isinstance(value, dict) else None
            )
        return self._cache.get(key)

    async def _set_impl(
        self,
        guild_id: int,
        audit_log_id: int | None = _MISSING,
        mod_log_id: int | None = _MISSING,
        jail_role_id: int | None = _MISSING,
        jail_channel_id: int | None = _MISSING,
    ) -> None:
        """Merge and write guild config (caller holds lock if needed)."""
        key = self._cache_key(guild_id)
        if self._backend is not None:
            raw = await self._backend.get(key)
            existing: dict[str, int | None] = (
                cast(dict[str, int | None], raw) if isinstance(raw, dict) else {}
            )
        else:
            existing = cast(
                dict[str, int | None],
                self._cache.get(key) or {},
            )
        updated: dict[str, int | None] = dict(existing)
        if audit_log_id is not _MISSING:
            updated["audit_log_id"] = audit_log_id
        if mod_log_id is not _MISSING:
            updated["mod_log_id"] = mod_log_id
        if jail_role_id is not _MISSING:
            updated["jail_role_id"] = jail_role_id
        if jail_channel_id is not _MISSING:
            updated["jail_channel_id"] = jail_channel_id
        if self._backend is not None:
            await self._backend.set(key, updated, ttl_sec=GUILD_CONFIG_TTL_SEC)
        else:
            self._cache.set(key, updated)

    async def set(
        self,
        guild_id: int,
        audit_log_id: int | None = _MISSING,
        mod_log_id: int | None = _MISSING,
        jail_role_id: int | None = _MISSING,
        jail_channel_id: int | None = _MISSING,
        *,
        use_lock: bool = False,
    ) -> None:
        """
        Cache guild config for a guild (partial merge).

        Parameters
        ----------
        guild_id : int
            The guild ID.
        audit_log_id : int | None, optional
            The audit log channel ID. Omit to skip updating this field.
        mod_log_id : int | None, optional
            The mod log channel ID. Omit to skip updating this field.
        jail_role_id : int | None, optional
            The jail role ID. Omit to skip updating this field.
        jail_channel_id : int | None, optional
            The jail channel ID. Omit to skip updating this field.
        use_lock : bool, optional
            If True, acquire per-guild lock before read-merge-write (for concurrent
            safety). Use when multiple coroutines may update the same guild.
        """
        if use_lock:
            async with await self._get_lock(guild_id):
                await self._set_impl(
                    guild_id,
                    audit_log_id=audit_log_id,
                    mod_log_id=mod_log_id,
                    jail_role_id=jail_role_id,
                    jail_channel_id=jail_channel_id,
                )
        else:
            await self._set_impl(
                guild_id,
                audit_log_id=audit_log_id,
                mod_log_id=mod_log_id,
                jail_role_id=jail_role_id,
                jail_channel_id=jail_channel_id,
            )

    async def async_set(
        self,
        guild_id: int,
        audit_log_id: int | None = _MISSING,
        mod_log_id: int | None = _MISSING,
        jail_role_id: int | None = _MISSING,
        jail_channel_id: int | None = _MISSING,
    ) -> None:
        """Cache guild config for a guild with async locking (concurrent safety).

        Parameters
        ----------
        guild_id : int
            The guild ID.
        audit_log_id : int | None, optional
            The audit log channel ID. Omit to skip updating this field.
        mod_log_id : int | None, optional
            The mod log channel ID. Omit to skip updating this field.
        jail_role_id : int | None, optional
            The jail role ID. Omit to skip updating this field.
        jail_channel_id : int | None, optional
            The jail channel ID. Omit to skip updating this field.
        """
        await self.set(
            guild_id,
            audit_log_id=audit_log_id,
            mod_log_id=mod_log_id,
            jail_role_id=jail_role_id,
            jail_channel_id=jail_channel_id,
            use_lock=True,
        )

    async def invalidate(self, guild_id: int) -> None:
        """
        Invalidate cached guild config for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to invalidate.
        """
        key = self._cache_key(guild_id)
        if self._backend is not None:
            await self._backend.delete(key)
        else:
            self._cache.invalidate(key)
        logger.debug("Invalidated guild config cache for guild {}", guild_id)

    async def clear_all(self) -> None:
        """Clear all cached guild config entries.

        Notes
        -----
        Only the in-memory cache is cleared; when a backend is configured,
        backend keys are not deleted (no pattern delete).
        """
        self._cache.clear()
        logger.debug("Cleared all guild config cache entries")


class JailStatusCache:
    """
    Cache manager for jail status checks.

    Provides a singleton instance that caches jail status per (guild_id, user_id)
    tuple. Supports optional AsyncCacheBackend (e.g. Valkey).
    """

    __slots__ = ("_backend", "_cache", "_locks", "_locks_lock")
    _instance: JailStatusCache | None = None
    _cache: TTLCache
    _locks: dict[tuple[int, int], asyncio.Lock]
    _locks_lock: asyncio.Lock
    _backend: AsyncCacheBackend | None

    def __new__(cls) -> JailStatusCache:
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = TTLCache(ttl=JAIL_STATUS_TTL_SEC, max_size=5000)
            cls._instance._locks = {}
            cls._instance._locks_lock = asyncio.Lock()
            cls._instance._backend = None
        return cls._instance

    def set_backend(self, backend: AsyncCacheBackend) -> None:
        """Set the cache backend.

        Parameters
        ----------
        backend : AsyncCacheBackend
            Backend instance to use for cache operations.
        """
        self._backend = backend
        logger.debug(
            "JailStatusCache backend set to {}",
            type(backend).__name__,
        )

    def _get_lock_key(self, guild_id: int, user_id: int) -> tuple[int, int]:
        """Generate lock key for guild_id and user_id."""
        return (guild_id, user_id)

    async def _get_lock(self, guild_id: int, user_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific (guild_id, user_id) pair."""
        lock_key = self._get_lock_key(guild_id, user_id)
        async with self._locks_lock:
            if lock_key not in self._locks:
                self._locks[lock_key] = asyncio.Lock()
        return self._locks[lock_key]

    def _cache_key(self, guild_id: int, user_id: int) -> str:
        """Return the cache key (backend adds tux: prefix)."""
        return f"jail_status:{guild_id}:{user_id}"

    async def get(self, guild_id: int, user_id: int) -> bool | None:
        """
        Get cached jail status for a user.

        Returns
        -------
        bool | None
            True if jailed, False if not jailed, None if not cached.
        """
        key = self._cache_key(guild_id, user_id)
        if self._backend is not None:
            value = await self._backend.get(key)
            if value is None:
                return None
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value in ("1", "true", "True")
            return bool(value)
        return self._cache.get(key)

    async def set(self, guild_id: int, user_id: int, is_jailed: bool) -> None:
        """Cache jail status for a user.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        is_jailed : bool
            Whether the user is jailed.
        """
        key = self._cache_key(guild_id, user_id)
        if self._backend is not None:
            await self._backend.set(key, is_jailed, ttl_sec=JAIL_STATUS_TTL_SEC)
        else:
            self._cache.set(key, is_jailed)

    async def get_or_fetch(
        self,
        guild_id: int,
        user_id: int,
        fetch_func: Callable[[], Coroutine[Any, Any, bool]],
    ) -> bool:
        """Get cached value or fetch and cache with async locking (stampede protection).

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        fetch_func : Callable[[], Coroutine[Any, Any, bool]]
            Async callable that returns the jail status when cache misses.

        Returns
        -------
        bool
            Cached or freshly fetched jail status.
        """
        cached_status = await self.get(guild_id, user_id)
        if cached_status is not None:
            return cached_status

        lock = await self._get_lock(guild_id, user_id)
        async with lock:
            cached_status = await self.get(guild_id, user_id)
            if cached_status is not None:
                return cached_status
            is_jailed = await fetch_func()
            await self.set(guild_id, user_id, is_jailed)
            return is_jailed

    async def async_set(self, guild_id: int, user_id: int, is_jailed: bool) -> None:
        """Cache jail status with async locking; overwrites any existing value.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        is_jailed : bool
            Whether the user is jailed.
        """
        key = self._cache_key(guild_id, user_id)
        lock = await self._get_lock(guild_id, user_id)
        async with lock:
            if self._backend is not None:
                await self._backend.set(key, is_jailed, ttl_sec=JAIL_STATUS_TTL_SEC)
            else:
                self._cache.set(key, is_jailed)

    async def invalidate(self, guild_id: int, user_id: int) -> None:
        """Invalidate cached jail status for a user.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        """
        key = self._cache_key(guild_id, user_id)
        if self._backend is not None:
            await self._backend.delete(key)
        else:
            self._cache.invalidate(key)
        logger.debug(
            "Invalidated jail status cache for guild {}, user {}",
            guild_id,
            user_id,
        )

    async def invalidate_guild(self, guild_id: int) -> None:
        """Invalidate in-memory jail status entries for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to invalidate.

        Notes
        -----
        Only the in-memory cache is cleared for this guild; when a backend
        (e.g. Valkey) is configured, backend keys for this guild are not
        deleted. For full clear use :meth:`clear_all` (in-memory only).
        """
        prefix = f"jail_status:{guild_id}:"
        removed = self._cache.invalidate_keys_matching(
            lambda key: str(key).startswith(prefix),
        )
        logger.debug(
            "Invalidated {} jail status cache entries for guild {}",
            removed,
            guild_id,
        )

    async def clear_all(self) -> None:
        """Clear all cached jail status entries (in-memory only).

        Notes
        -----
        When a backend is configured, backend keys are not deleted.
        """
        self._cache.clear()
        logger.debug("Cleared all jail status cache entries")
