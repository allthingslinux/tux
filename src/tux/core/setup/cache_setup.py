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
        """Set up the cache backend for the bot.

        Returns
        -------
        None
            Initializes `cache_service` and never raises.

        Notes
        -----
        If VALKEY_URL (or VALKEY_HOST) is empty, the bot uses in-memory caches.
        If connection or ping fails, the bot logs a warning and continues with
        in-memory caches.
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
                    self.bot.cache_service = None
            except Exception as e:
                logger.warning(
                    "Valkey connection failed ({}); using in-memory caches only",
                    e,
                )
                self.bot.cache_service = None
            finally:
                if self.bot.cache_service is None:
                    await service.close()

        # Wire cache backend into singletons (Valkey if connected, else in-memory)
        backend = get_cache_backend(self.bot)
        GuildConfigCacheManager().set_backend(backend)
        JailStatusCache().set_backend(backend)
        logger.debug("Cache backend wired: {}", type(backend).__name__)
