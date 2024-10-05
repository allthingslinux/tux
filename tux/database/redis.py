import redis.asyncio as redis
from loguru import logger


class RedisManager:
    def __init__(self):
        self.interface: redis.Redis = redis.Redis()

    async def connect(self, url: str) -> None:
        """
        Connect to the Redis server.

        Parameters
        ----------
        url : str
            The URL of the Redis server to connect to.
        """
        try:
            self.redis = redis.from_url(url, decode_responses=True)  # type: ignore
            await self.redis.ping()  # type: ignore
            logger.info("Successfully connected to Redis")

        except redis.ConnectionError as e:
            logger.warning(f"Failed to connect to Redis: {e}")


redis_manager = RedisManager()
