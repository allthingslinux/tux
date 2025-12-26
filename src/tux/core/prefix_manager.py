"""
Prefix management with in-memory caching for optimal performance.

This module provides efficient prefix resolution for Discord commands by maintaining
an in-memory cache of guild prefixes, eliminating database hits on every message.

The PrefixManager uses a cache-first approach:

1. Check environment variable override (BOT_INFO__PREFIX)
2. Check in-memory cache (O(1) lookup)
3. Load from database on cache miss
4. Persist changes asynchronously to avoid blocking

This architecture ensures sub-millisecond prefix lookups after initial cache load.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from tux.database.utils import get_db_controller_from
from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from tux.core.bot import Tux

__all__ = ["PrefixManager"]


class PrefixManager:
    """
    Manages command prefixes with in-memory caching.

    Provides O(1) prefix lookups after initial cache load through lazy loading
    and automatic caching. See module docstring for resolution priority order.

    Attributes
    ----------
    bot : Tux
        The bot instance this manager is attached to.
    _prefix_cache : dict[int, str]
        In-memory cache mapping guild IDs to prefixes.
    _cache_loaded : bool
        Whether the initial cache load has completed.
    _default_prefix : str
        Default prefix from configuration.
    _loading_lock : asyncio.Lock
        Lock to prevent concurrent cache loading.
    """

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the prefix manager.

        Parameters
        ----------
        bot : Tux
            The bot instance to manage prefixes for.
        """
        self.bot = bot
        self._prefix_cache: dict[int, str] = {}
        self._cache_loaded = False
        self._default_prefix = CONFIG.get_prefix()
        self._loading_lock = asyncio.Lock()

        logger.debug("PrefixManager initialized")

    async def get_prefix(self, guild_id: int | None) -> str:
        """
        Get the command prefix for a guild or DM.

        Follows the resolution priority documented in the module docstring.
        Automatically caches results for O(1) subsequent lookups.

        Parameters
        ----------
        guild_id : int | None
            The Discord guild ID, or None for DMs.

        Returns
        -------
        str
            The command prefix, or default prefix if not found.
        """
        if CONFIG.is_prefix_override_enabled():
            return self._default_prefix

        if guild_id is None:
            return self._default_prefix

        if guild_id in self._prefix_cache:
            return self._prefix_cache[guild_id]

        return await self._load_guild_prefix(guild_id)

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Set the command prefix for a guild.

        Updates cache immediately and persists to database asynchronously.
        No-op if prefix override is enabled via environment variable.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The new command prefix to set.
        """
        if CONFIG.is_prefix_override_enabled():
            logger.warning(
                f"Prefix override enabled - ignoring prefix change for guild {guild_id} to '{prefix}'. All guilds use default prefix '{self._default_prefix}'",
            )
            return

        self._prefix_cache[guild_id] = prefix

        # Fire-and-forget: persist to database asynchronously
        asyncio.create_task(self._persist_prefix(guild_id, prefix))  # noqa: RUF006

        logger.info(f"Prefix updated for guild {guild_id}: '{prefix}'")

    async def _load_guild_prefix(self, guild_id: int) -> str:
        """
        Load a guild's prefix from the database and cache it.

        Called on cache misses. Ensures guild exists, loads or creates config,
        and caches the result. Always returns a prefix (never raises).

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        str
            The guild's prefix, or default prefix if loading fails.
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; using default prefix")
                return self._default_prefix

            await controller.guild.get_or_create_guild(guild_id)

            guild_config = await controller.guild_config.get_or_create_config(
                guild_id,
                prefix=self._default_prefix,
            )

            prefix = guild_config.prefix
            self._prefix_cache[guild_id] = prefix

        except Exception as e:
            logger.warning(
                f"Failed to load prefix for guild {guild_id}: {type(e).__name__}",
            )
            return self._default_prefix
        else:
            return prefix

    async def _persist_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Persist a prefix change to the database.

        Runs as a background task after set_prefix. Removes cache entry on
        failure to maintain consistency. Never raises.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The prefix to persist.
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; prefix change not persisted")
                return

            await controller.guild.get_or_create_guild(guild_id)
            await controller.guild_config.update_config(guild_id, prefix=prefix)

            logger.debug(f"Prefix persisted for guild {guild_id}: '{prefix}'")

        except Exception as e:
            logger.error(
                f"Failed to persist prefix for guild {guild_id}: {type(e).__name__}",
            )
            # Remove from cache on failure to maintain consistency
            self._prefix_cache.pop(guild_id, None)

    async def load_all_prefixes(self) -> None:
        """
        Load all guild prefixes into cache at startup.

        Called during bot initialization. Uses a lock to prevent concurrent
        loading, has a 10-second timeout, and loads up to 1000 configs.
        Idempotent and safe to call multiple times.
        """
        if self._cache_loaded:
            return

        async with self._loading_lock:
            if self._cache_loaded:
                return

            try:
                controller = get_db_controller_from(self.bot, fallback_to_direct=False)
                if controller is None:
                    logger.warning("Database unavailable; prefix cache not loaded")
                    self._cache_loaded = True
                    return

                logger.debug("Loading all guild prefixes into cache...")
                all_configs = await asyncio.wait_for(
                    controller.guild_config.find_all(limit=1000),
                    timeout=10.0,
                )

                for config in all_configs:
                    self._prefix_cache[config.id] = config.prefix

                self._cache_loaded = True
                logger.info(
                    f"Loaded {len(self._prefix_cache)} guild prefixes into cache",
                )

            except TimeoutError:
                logger.warning(
                    "Timeout loading prefix cache - continuing without cache",
                )
                self._cache_loaded = True

            except Exception as e:
                logger.error(f"Failed to load prefix cache: {type(e).__name__}")
                self._cache_loaded = True

    def invalidate_cache(self, guild_id: int | None = None) -> None:
        """
        Invalidate prefix cache for a specific guild or all guilds.

        Parameters
        ----------
        guild_id : int | None, optional
            The guild ID to invalidate, or None to invalidate all.
            Defaults to None.

        Examples
        --------
        >>> manager.invalidate_cache(123456789)  # Specific guild
        >>> manager.invalidate_cache()  # All guilds
        """
        if guild_id is None:
            self._prefix_cache.clear()
            self._cache_loaded = False
            logger.debug("All prefix cache invalidated")
        else:
            self._prefix_cache.pop(guild_id, None)
            logger.debug(f"Prefix cache invalidated for guild {guild_id}")

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics for monitoring and debugging.

        Returns
        -------
        dict[str, int]
            Dictionary with keys:
            - cached_prefixes: Number of guilds in cache
            - cache_loaded: 1 if initial load completed, 0 otherwise
        """
        return {
            "cached_prefixes": len(self._prefix_cache),
            "cache_loaded": int(self._cache_loaded),
        }
