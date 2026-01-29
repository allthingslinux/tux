"""Cache (Valkey) setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.cache import (
    CacheService,
    GuildConfigCacheManager,
    JailStatusCache,
    get_cache_backend,
)
from tux.core.setup.base import BotSetupService
from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = ["CacheSetupService"]


class CacheSetupService(BotSetupService):
    """Handles optional Valkey cache connection during bot setup."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the cache setup service.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance to set up.
        """
        super().__init__(bot, "cache")

    async def setup(self) -> None:
        """
        Connect to Valkey when configured; otherwise leave cache_service as None.

        If VALKEY_URL (or VALKEY_HOST) is empty, bot.cache_service is set to None
        and the bot continues without Valkey (in-memory caches only). If the URL
        is set but connection or ping fails, log and set bot.cache_service = None
        so the bot still starts. Never raises.
        """
        if not CONFIG.valkey_url:
            self.bot.cache_service = None
            logger.debug("Valkey not configured; using in-memory caches only")
        else:
            service = CacheService()
            try:
                await service.connect()
                if await service.ping():
                    self.bot.cache_service = service
                    logger.success("Cache (Valkey) setup completed")
                else:
                    logger.warning("Valkey ping failed; using in-memory caches only")
                    await service.close()
                    self.bot.cache_service = None
            except Exception as e:
                logger.warning(
                    f"Valkey connection failed ({e}); using in-memory caches only",
                )
                self.bot.cache_service = None

        # Wire cache backend into singletons (Valkey if connected, else in-memory)
        backend = get_cache_backend(self.bot)
        GuildConfigCacheManager().set_backend(backend)
        JailStatusCache().set_backend(backend)
        logger.debug("Cache backend wired: {}", type(backend).__name__)
