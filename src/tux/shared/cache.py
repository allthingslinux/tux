"""
TTL-based caching utility for frequently accessed data.

Provides a simple, thread-safe TTL cache implementation for caching
guild configuration and other data that changes infrequently.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

from loguru import logger

# Sentinel value to indicate a field was not provided
_MISSING: Any = object()

__all__ = ["TTLCache", "GuildConfigCacheManager", "JailStatusCache"]


class TTLCache:
    """
    Thread-safe TTL cache with automatic expiration.

    Caches values with a time-to-live (TTL) in seconds. Expired entries
    are automatically removed on access. Supports cache invalidation.

    Attributes
    ----------
    ttl : float
        Time-to-live for cache entries in seconds.
    max_size : int | None
        Maximum number of entries. If None, no limit.
    """

    __slots__ = ("_cache", "_max_size", "_ttl")

    def __init__(self, ttl: float = 300.0, max_size: int | None = None) -> None:
        """
        Initialize the TTL cache.

        Parameters
        ----------
        ttl : float, optional
            Time-to-live in seconds, by default 300.0 (5 minutes).
        max_size : int | None, optional
            Maximum number of entries. If None, no limit, by default None.
        """
        self._cache: dict[Any, tuple[Any, float]] = {}
        self._ttl = ttl
        self._max_size = max_size

    def get(self, key: Any) -> Any | None:
        """
        Get a value from the cache.

        Returns None if the key doesn't exist or has expired.
        Automatically removes expired entries.

        Parameters
        ----------
        key : Any
            The cache key.

        Returns
        -------
        Any | None
            The cached value, or None if not found or expired.

        Notes
        -----
        This method is safe for concurrent async access. In Python's async model
        (single-threaded event loop), dict operations are atomic. The check-then-act
        pattern here has no await points, so no other coroutine can run between
        the check and the access, making it race-condition safe.
        """
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]
        if time.monotonic() > expire_time:
            # Expired, remove it
            del self._cache[key]
            logger.trace(f"Cache entry expired for key: {key}")
            return None

        return value

    def set(self, key: Any, value: Any) -> None:
        """
        Set a value in the cache.

        Parameters
        ----------
        key : Any
            The cache key.
        value : Any
            The value to cache.
        """
        # Evict oldest entries if at max size
        if self._max_size is not None and len(self._cache) >= self._max_size:
            # Remove oldest entry (simple FIFO eviction)
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            logger.trace(f"Cache evicted oldest entry: {oldest_key}")

        expire_time = time.monotonic() + self._ttl
        self._cache[key] = (value, expire_time)
        logger.trace(f"Cache entry set for key: {key} (expires in {self._ttl}s)")

    def invalidate(self, key: Any | None = None) -> None:
        """
        Invalidate cache entries.

        Parameters
        ----------
        key : Any | None, optional
            Specific key to invalidate, or None to clear all entries.
            Defaults to None.
        """
        if key is None:
            count = len(self._cache)
            self._cache.clear()
            logger.debug(f"Cache cleared: {count} entries removed")
        elif key in self._cache:
            del self._cache[key]
            logger.trace(f"Cache entry invalidated: {key}")

    def get_or_fetch(
        self,
        key: Any,
        fetch_fn: Callable[[], Any],
    ) -> Any:
        """
        Get a value from cache or fetch it if not present.

        Parameters
        ----------
        key : Any
            The cache key.
        fetch_fn : Callable[[], Any]
            Function to fetch the value if not in cache.

        Returns
        -------
        Any
            The cached or fetched value.
        """
        cached = self.get(key)
        if cached is not None:
            return cached

        value = fetch_fn()
        self.set(key, value)
        return value

    def size(self) -> int:
        """
        Get the current number of entries in the cache.

        Returns
        -------
        int
            Number of cache entries.
        """
        # Clean expired entries first
        now = time.monotonic()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items() if now > expire_time
        ]
        for key in expired_keys:
            del self._cache[key]

        return len(self._cache)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.invalidate()


class GuildConfigCacheManager:
    """
    Shared cache manager for guild configuration data.

    Provides a singleton instance that can be used across the application
    to cache and invalidate guild configuration data, ensuring consistency
    when config is updated from multiple sources.
    """

    __slots__ = ("_cache", "_locks")
    _instance: GuildConfigCacheManager | None = None
    _cache: TTLCache
    _locks: dict[int, asyncio.Lock]

    def __new__(cls) -> GuildConfigCacheManager:
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = TTLCache(ttl=600.0, max_size=1000)  # 10 min
            cls._instance._locks = {}  # Per-guild locks for cache updates
        return cls._instance

    def _get_lock(self, guild_id: int) -> asyncio.Lock:
        """Get or create a lock for a specific guild."""
        if guild_id not in self._locks:
            self._locks[guild_id] = asyncio.Lock()
        return self._locks[guild_id]

    def get(self, guild_id: int) -> dict[str, int | None] | None:
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
        cache_key = f"guild_config_{guild_id}"
        return self._cache.get(cache_key)

    def set(
        self,
        guild_id: int,
        audit_log_id: int | None = _MISSING,
        mod_log_id: int | None = _MISSING,
        jail_role_id: int | None = _MISSING,
        jail_channel_id: int | None = _MISSING,
    ) -> None:
        """
        Cache guild config for a guild.

        This method is safe for concurrent access. Multiple coroutines can
        call this with partial updates without losing data.

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

        Notes
        -----
        This method is synchronous and has no await points, making it atomic
        in Python's async model. However, when called from async code that
        has await points between cache check and set, use async_set() instead.
        """
        cache_key = f"guild_config_{guild_id}"
        # Get existing cache or create new dict
        existing: dict[str, int | None] = self._cache.get(cache_key) or {}
        # Start with existing values
        updated: dict[str, int | None] = dict(existing)

        # Only update fields that were explicitly provided (not _MISSING)
        if audit_log_id is not _MISSING:
            updated["audit_log_id"] = audit_log_id
        if mod_log_id is not _MISSING:
            updated["mod_log_id"] = mod_log_id
        if jail_role_id is not _MISSING:
            updated["jail_role_id"] = jail_role_id
        if jail_channel_id is not _MISSING:
            updated["jail_channel_id"] = jail_channel_id

        self._cache.set(cache_key, updated)

    async def async_set(
        self,
        guild_id: int,
        audit_log_id: int | None = _MISSING,
        mod_log_id: int | None = _MISSING,
        jail_role_id: int | None = _MISSING,
        jail_channel_id: int | None = _MISSING,
    ) -> None:
        """
        Cache guild config for a guild with async locking.

        Use this method when called from async code that has await points
        between cache check and set, to prevent race conditions with concurrent
        partial updates.

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
        lock = self._get_lock(guild_id)
        async with lock:
            # Re-check cache after acquiring lock (another coroutine may have updated it)
            cache_key = f"guild_config_{guild_id}"
            existing: dict[str, int | None] = self._cache.get(cache_key) or {}
            updated: dict[str, int | None] = dict(existing)

            # Only update fields that were explicitly provided (not _MISSING)
            if audit_log_id is not _MISSING:
                updated["audit_log_id"] = audit_log_id
            if mod_log_id is not _MISSING:
                updated["mod_log_id"] = mod_log_id
            if jail_role_id is not _MISSING:
                updated["jail_role_id"] = jail_role_id
            if jail_channel_id is not _MISSING:
                updated["jail_channel_id"] = jail_channel_id

            self._cache.set(cache_key, updated)

    def invalidate(self, guild_id: int) -> None:
        """
        Invalidate cached guild config for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID to invalidate.
        """
        cache_key = f"guild_config_{guild_id}"
        self._cache.invalidate(cache_key)
        logger.debug(f"Invalidated guild config cache for guild {guild_id}")

    def clear_all(self) -> None:
        """Clear all cached guild config entries."""
        self._cache.clear()
        logger.debug("Cleared all guild config cache entries")


class JailStatusCache:
    """
    Cache manager for jail status checks.

    Provides a singleton instance that caches jail status per (guild_id, user_id)
    tuple to reduce database queries for frequently checked jail status.
    """

    __slots__ = ("_cache", "_locks", "_locks_lock")
    _instance: JailStatusCache | None = None
    _cache: TTLCache
    _locks: dict[tuple[int, int], asyncio.Lock]
    _locks_lock: asyncio.Lock

    def __new__(cls) -> JailStatusCache:
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 5 min TTL - jail status changes infrequently
            cls._instance._cache = TTLCache(ttl=300.0, max_size=5000)
            cls._instance._locks = {}  # Per (guild_id, user_id) locks for cache updates
            cls._instance._locks_lock = (
                asyncio.Lock()
            )  # Lock for managing the locks dict
        return cls._instance

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

    async def get_or_fetch(
        self,
        guild_id: int,
        user_id: int,
        fetch_func: Callable[[], Coroutine[Any, Any, bool]],
    ) -> bool:
        """
        Get cached value or fetch and cache with async locking.

        Prevents cache stampede when multiple coroutines miss the cache
        simultaneously. Only one coroutine will fetch, others will wait
        and use the cached result.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        fetch_func : Callable[[], Coroutine[Any, Any, bool]]
            Async function to fetch the value if not cached.

        Returns
        -------
        bool
            The cached or fetched jail status.
        """
        # Check cache first (fast path)
        cached_status = self.get(guild_id, user_id)
        if cached_status is not None:
            return cached_status

        # Cache miss - acquire lock to prevent stampede
        lock = await self._get_lock(guild_id, user_id)
        async with lock:
            # Re-check cache after acquiring lock
            cached_status = self.get(guild_id, user_id)
            if cached_status is not None:
                return cached_status

            # Still a cache miss - fetch from database
            is_jailed = await fetch_func()

            # Cache the result (atomic operation, no await points)
            self.set(guild_id, user_id, is_jailed)
            return is_jailed

    def _get_key(self, guild_id: int, user_id: int) -> str:
        """Generate cache key for guild_id and user_id."""
        return f"jail_status_{guild_id}_{user_id}"

    def get(self, guild_id: int, user_id: int) -> bool | None:
        """
        Get cached jail status for a user.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.

        Returns
        -------
        bool | None
            True if jailed, False if not jailed, None if not cached.
        """
        cache_key = self._get_key(guild_id, user_id)
        return self._cache.get(cache_key)

    def set(self, guild_id: int, user_id: int, is_jailed: bool) -> None:
        """
        Cache jail status for a user.

        This method is safe for concurrent access. Multiple coroutines can
        call this without losing data.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        is_jailed : bool
            Whether the user is jailed.

        Notes
        -----
        This method is synchronous and has no await points, making it atomic
        in Python's async model. However, when called from async code that
        has await points between cache check and set, use async_set() instead.
        """
        cache_key = self._get_key(guild_id, user_id)
        self._cache.set(cache_key, is_jailed)

    async def async_set(self, guild_id: int, user_id: int, is_jailed: bool) -> None:
        """
        Cache jail status for a user with async locking.

        Use this method when called from async code that has await points
        between cache check and set, to prevent cache stampede when multiple
        coroutines miss the cache simultaneously.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        is_jailed : bool
            Whether the user is jailed.
        """
        lock = await self._get_lock(guild_id, user_id)
        async with lock:
            # Re-check cache after acquiring lock (another coroutine may have updated it)
            cache_key = self._get_key(guild_id, user_id)
            cached = self._cache.get(cache_key)
            if cached is not None:
                # Another coroutine already cached the value, no need to set again
                return
            self._cache.set(cache_key, is_jailed)

    def invalidate(self, guild_id: int, user_id: int) -> None:
        """
        Invalidate cached jail status for a user.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        user_id : int
            The user ID.
        """
        cache_key = self._get_key(guild_id, user_id)
        self._cache.invalidate(cache_key)
        logger.debug(
            f"Invalidated jail status cache for guild {guild_id}, user {user_id}",
        )

    def invalidate_guild(self, guild_id: int) -> None:
        """
        Invalidate all jail status cache entries for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        """
        # Note: This is a simple implementation. For better performance with many entries,
        # we could maintain a reverse index, but for now we'll just clear all entries.
        # The TTL will naturally expire entries anyway.
        self._cache.clear()
        logger.debug(
            f"Cleared all jail status cache entries (guild {guild_id} invalidation)",
        )

    def clear_all(self) -> None:
        """Clear all cached jail status entries."""
        self._cache.clear()
        logger.debug("Cleared all jail status cache entries")
