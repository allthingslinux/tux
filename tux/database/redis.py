from collections.abc import Callable
from typing import Any

import redis.asyncio as redis
from loguru import logger

from tux.utils.constants import CONST


class RedisManager:
    def __init__(self):
        self.redis: redis.Redis | None = None
        self.is_connected: bool = False
        self.debug_log: Callable[[str], None] = logger.debug if CONST.REDIS_DEBUG_LOG else lambda msg: None

    async def connect(self, url: str) -> None:
        try:
            self.redis = redis.from_url(url, decode_responses=True)  # type: ignore
            await self.redis.ping()  # type: ignore
            self.is_connected = True
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.is_connected = False

    async def disconnect(self) -> None:
        if self.redis:
            await self.redis.close()
            self.is_connected = False
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> str | None:
        if self.redis and self.is_connected:
            value = await self.redis.get(key)
            self.debug_log(f"Retrieved key '{key}' with value '{value}' from Redis")
            return value
        self.debug_log(f"Failed to retrieve key '{key}' from Redis")
        return None

    async def set(self, key: str, value: str, expiration: int | None = None) -> None:
        if self.redis and self.is_connected:
            await self.redis.set(key, value, ex=expiration)
            self.debug_log(f"Set key '{key}' with value '{value}' in Redis with expiration '{expiration}'")

    async def delete(self, key: str) -> None:
        if self.redis and self.is_connected:
            await self.redis.delete(key)
            self.debug_log(f"Deleted key '{key}' from Redis")

    async def increment(self, key: str, amount: int = 1) -> int | None:
        if self.redis and self.is_connected:
            new_value = await self.redis.incr(key, amount)
            self.debug_log(f"Incremented key '{key}' by '{amount}', new value is '{new_value}'")
            return new_value
        self.debug_log(f"Failed to increment key '{key}' by '{amount}'")
        return None

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if self.redis and self.is_connected:
            await self.redis.zadd(key, mapping)
            self.debug_log(f"Added to sorted set '{key}' with mapping '{mapping}'")

    async def zrange(self, key: str, start: int, end: int, desc: bool = False, withscores: bool = False) -> list[Any]:
        if self.redis and self.is_connected:
            result = await self.redis.zrange(key, start, end, desc=desc, withscores=withscores)  # type: ignore
            self.debug_log(
                f"Retrieved range from sorted set '{key}' from '{start}' to '{end}', desc='{desc}', withscores='{withscores}': {result}",
            )
            return result
        self.debug_log(f"Failed to retrieve range from sorted set '{key}' from '{start}' to '{end}'")
        return []


redis_manager = RedisManager()
