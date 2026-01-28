"""Cache backend abstraction: in-memory and Valkey implementations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Protocol

from loguru import logger

from tux.cache.ttl import TTLCache

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = [
    "AsyncCacheBackend",
    "InMemoryBackend",
    "ValkeyBackend",
    "get_cache_backend",
]

KEY_PREFIX = "tux:"


class AsyncCacheBackend(Protocol):
    """Protocol for async cache backends (in-memory or Valkey)."""

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Return None if missing or expired."""
        ...

    async def set(
        self,
        key: str,
        value: Any,
        ttl_sec: float | None = None,
    ) -> None:
        """Set a value with optional TTL."""
        ...

    async def delete(self, key: str) -> None:
        """Delete a key."""
        ...

    async def exists(self, key: str) -> bool:
        """Return True if key exists and is not expired."""
        ...


class InMemoryBackend:
    """
    In-memory cache backend using TTLCache.

    Used when Valkey is not configured or unavailable. Values are stored
    as-is (no JSON serialization) for compatibility with existing TTLCache usage.
    """

    def __init__(
        self,
        default_ttl: float = 300.0,
        max_size: int | None = 10000,
    ) -> None:
        """Initialize the in-memory backend.

        Parameters
        ----------
        default_ttl : float, optional
            Default TTL in seconds when set() is called without ttl_sec.
        max_size : int | None, optional
            Max entries (FIFO eviction). None for no limit.
        """
        self._cache: TTLCache = TTLCache(ttl=default_ttl, max_size=max_size)
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        """Get a value by key."""
        return self._cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_sec: float | None = None,
    ) -> None:
        """Set a value with optional TTL."""
        self._cache.set(key, value)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        self._cache.invalidate(key)

    async def exists(self, key: str) -> bool:
        """Return True if key exists and is not expired."""
        return self._cache.get(key) is not None


class ValkeyBackend:
    """
    Valkey (Redis-compatible) cache backend.

    Keys are prefixed with `tux:`. Values are JSON-serialized.
    TTL is set via SETEX when ttl_sec is provided.
    """

    def __init__(self, client: Any) -> None:
        """Initialize the Valkey backend.

        Parameters
        ----------
        client : Any
            Async Valkey client (valkey.asyncio.Valkey) with decode_responses=True.
        """
        self._client = client
        self._prefix = KEY_PREFIX

    def _key(self, key: str) -> str:
        """Return the full key with prefix."""
        if key.startswith(self._prefix):
            return key
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Get a value by key. Deserializes JSON."""
        full_key = self._key(key)
        raw = await self._client.get(full_key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.debug(
                "Valkey key returned non-JSON value, returning raw",
                key=key,
            )
            return raw

    async def set(
        self,
        key: str,
        value: Any,
        ttl_sec: float | None = None,
    ) -> None:
        """Set a value with optional TTL. Serializes to JSON."""
        full_key = self._key(key)
        payload = value if isinstance(value, str) else json.dumps(value)
        if ttl_sec is not None and ttl_sec > 0:
            await self._client.setex(full_key, int(ttl_sec), payload)
        else:
            await self._client.set(full_key, payload)

    async def delete(self, key: str) -> None:
        """Delete a key."""
        full_key = self._key(key)
        await self._client.delete(full_key)

    async def exists(self, key: str) -> bool:
        """Return True if key exists."""
        full_key = self._key(key)
        return bool(await self._client.exists(full_key))


_FALLBACK_BACKEND_ATTR = "_fallback_cache_backend"


def get_cache_backend(bot: Tux) -> AsyncCacheBackend:
    """
    Return the cache backend for the bot (Valkey if connected, else in-memory).

    When Valkey is not configured or disconnected, a single shared InMemoryBackend
    is cached on the bot so all consumers (cache managers, prefix, permissions)
    use the same in-memory store.

    Parameters
    ----------
    bot : Tux
        The bot instance (must have cache_service set by setup).

    Returns
    -------
    AsyncCacheBackend
        ValkeyBackend if bot.cache_service is connected, else a shared InMemoryBackend.
    """
    cache_service = getattr(bot, "cache_service", None)
    if cache_service is not None and cache_service.is_connected():
        client = cache_service.get_client()
        if client is not None:
            return ValkeyBackend(client)
    fallback = getattr(bot, _FALLBACK_BACKEND_ATTR, None)
    if not isinstance(fallback, InMemoryBackend):
        logger.debug("Using in-memory cache backend (Valkey unavailable)")
        fallback = InMemoryBackend(default_ttl=300.0, max_size=10000)
        setattr(bot, _FALLBACK_BACKEND_ATTR, fallback)
    return fallback
