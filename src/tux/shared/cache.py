"""
TTL-based caching utility for frequently accessed data.

Provides a simple, thread-safe TTL cache implementation for caching
guild configuration and other data that changes infrequently.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from loguru import logger

__all__ = ["TTLCache", "GuildConfigCacheManager"]


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

    _instance: GuildConfigCacheManager | None = None
    _cache: TTLCache

    def __new__(cls) -> GuildConfigCacheManager:
        """Create or return the singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._cache = TTLCache(ttl=300.0, max_size=1000)
        return cls._instance

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
            Cached config dict with audit_log_id and mod_log_id, or None if not cached.
        """
        cache_key = f"guild_config_{guild_id}"
        return self._cache.get(cache_key)

    def set(
        self,
        guild_id: int,
        audit_log_id: int | None,
        mod_log_id: int | None,
    ) -> None:
        """
        Cache guild config for a guild.

        Parameters
        ----------
        guild_id : int
            The guild ID.
        audit_log_id : int | None
            The audit log channel ID.
        mod_log_id : int | None
            The mod log channel ID.
        """
        cache_key = f"guild_config_{guild_id}"
        self._cache.set(
            cache_key,
            {"audit_log_id": audit_log_id, "mod_log_id": mod_log_id},
        )

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
