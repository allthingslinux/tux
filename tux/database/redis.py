from typing import Any

import redis.asyncio as redis
from loguru import logger


class RedisManager:
    def __init__(self):
        self.redis: redis.Redis | None = None
        self.is_connected: bool = False

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
            logger.info(f"Retrieved key '{key}' with value '{value}' from Redis")
            return value
        logger.warning(f"Failed to retrieve key '{key}' from Redis")
        return None

    async def set(self, key: str, value: str, expiration: int | None = None) -> None:
        if self.redis and self.is_connected:
            await self.redis.set(key, value, ex=expiration)
            logger.info(f"Set key '{key}' with value '{value}' in Redis with expiration '{expiration}'")

    async def delete(self, key: str) -> None:
        if self.redis and self.is_connected:
            await self.redis.delete(key)
            logger.info(f"Deleted key '{key}' from Redis")

    async def increment(self, key: str, amount: int = 1) -> int | None:
        if self.redis and self.is_connected:
            new_value = await self.redis.incr(key, amount)
            logger.info(f"Incremented key '{key}' by '{amount}', new value is '{new_value}'")
            return new_value
        logger.warning(f"Failed to increment key '{key}' by '{amount}'")
        return None

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        if self.redis and self.is_connected:
            await self.redis.zadd(key, mapping)
            logger.info(f"Added to sorted set '{key}' with mapping '{mapping}'")

    async def zrange(self, key: str, start: int, end: int, desc: bool = False, withscores: bool = False) -> list[Any]:
        if self.redis and self.is_connected:
            result = await self.redis.zrange(key, start, end, desc=desc, withscores=withscores)  # type: ignore
            logger.info(
                f"Retrieved range from sorted set '{key}' from '{start}' to '{end}', desc='{desc}', withscores='{withscores}': {result}",
            )
            return result
        logger.warning(f"Failed to retrieve range from sorted set '{key}' from '{start}' to '{end}'")
        return []


redis_manager = RedisManager()
