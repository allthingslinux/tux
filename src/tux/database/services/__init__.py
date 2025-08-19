from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional

try:
    import redis.asyncio as redis  # type: ignore
except Exception:  # pragma: no cover - optional at runtime
    redis = None  # type: ignore


class CacheService:
    """Lightweight Redis caching service.

    Provides simple helpers used by controllers/services. Safe to import when
    Redis is unavailable (methods will no-op).
    """

    def __init__(self, redis_url: str | None = None) -> None:
        self._client = None
        if redis and redis_url:
            self._client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str) -> str | None:
        if self._client is None:
            return None
        return await self._client.get(key)

    async def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        if self._client is None:
            return
        await self._client.setex(key, ttl_seconds, value)

    async def delete(self, key: str) -> None:
        if self._client is None:
            return
        await self._client.delete(key)

    async def ttl(self, key: str) -> int | None:
        if self._client is None:
            return None
        return await self._client.ttl(key)
