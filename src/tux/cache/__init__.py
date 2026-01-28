"""Cache layer with optional Valkey (Redis-compatible) backend.

Provides CacheService, backends (InMemoryBackend, ValkeyBackend), TTL cache,
and cache managers (GuildConfigCacheManager, JailStatusCache).
"""

from tux.cache.backend import (
    AsyncCacheBackend,
    InMemoryBackend,
    ValkeyBackend,
    get_cache_backend,
)
from tux.cache.managers import GuildConfigCacheManager, JailStatusCache
from tux.cache.service import CacheService
from tux.cache.ttl import TTLCache

# Alias for code that still uses the old protocol name
AsyncCacheBackendProtocol = AsyncCacheBackend

__all__ = [
    "AsyncCacheBackend",
    "AsyncCacheBackendProtocol",
    "CacheService",
    "GuildConfigCacheManager",
    "InMemoryBackend",
    "JailStatusCache",
    "TTLCache",
    "ValkeyBackend",
    "get_cache_backend",
]
