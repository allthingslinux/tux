"""Prefix management with in-memory caching for optimal performance.

This module provides efficient prefix resolution for Discord commands by maintaining
an in-memory cache of guild prefixes, eliminating database hits on every message.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

from tux.database.utils import get_db_controller_from
from tux.shared.config import CONFIG

if TYPE_CHECKING:
    from tux.core.bot import Tux


class PrefixManager:
    """Manages command prefixes with in-memory caching for optimal performance.

    This class provides:
    - In-memory cache of guild prefixes
    - Lazy loading from database
    - Event-driven cache updates
    - Graceful fallback to default prefix
    - Zero database hits per message after initial load
    """

    def __init__(self, bot: Tux):
        """Initialize the prefix manager.

        Parameters
        ----------
        bot : Tux
            The bot instance to manage prefixes for
        """
        self.bot = bot
        self._prefix_cache: dict[int, str] = {}
        self._cache_loaded = False
        self._default_prefix = CONFIG.get_prefix()
        self._loading_lock = asyncio.Lock()

        logger.debug("PrefixManager initialized")

    async def get_prefix(self, guild_id: int) -> str:
        """Get the command prefix for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID

        Returns
        -------
        str
            The command prefix for the guild, or default prefix if not found
        """
        # Check if prefix override is enabled by environment variable
        if CONFIG.is_prefix_override_enabled():
            logger.debug(
                f"Prefix override enabled (BOT_INFO__PREFIX set), using default prefix '{self._default_prefix}' for guild {guild_id}",
            )
            return self._default_prefix

        # Check cache first (fast path)
        if guild_id in self._prefix_cache:
            return self._prefix_cache[guild_id]

        # Cache miss - load from database
        return await self._load_guild_prefix(guild_id)

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        """Set the command prefix for a guild.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID
        prefix : str
            The new command prefix
        """
        # Check if prefix override is enabled by environment variable - warn but don't update
        if CONFIG.is_prefix_override_enabled():
            logger.warning(
                f"Prefix override enabled (BOT_INFO__PREFIX set) - ignoring prefix change for guild {guild_id} to '{prefix}'. All guilds use default prefix '{self._default_prefix}'",
            )
            return

        # Update cache immediately
        self._prefix_cache[guild_id] = prefix

        # Persist to database asynchronously (don't block)
        persist_task = asyncio.create_task(self._persist_prefix(guild_id, prefix))
        # Store reference to prevent garbage collection
        _ = persist_task

        logger.info(f"Prefix updated for guild {guild_id}: '{prefix}'")

    async def _load_guild_prefix(self, guild_id: int) -> str:
        """Load a guild's prefix from the database.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID

        Returns
        -------
        str
            The guild's prefix or default prefix
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; using default prefix")
                return self._default_prefix

            # Ensure guild exists in database
            await controller.guild.get_or_create_guild(guild_id)

            # Get or create guild config
            guild_config = await controller.guild_config.get_or_create_config(guild_id, prefix=self._default_prefix)

            if guild_config and hasattr(guild_config, "prefix"):
                prefix = guild_config.prefix
                # Cache the result
                self._prefix_cache[guild_id] = prefix
                return prefix

        except Exception as e:
            logger.warning(f"Failed to load prefix for guild {guild_id}: {type(e).__name__}")

        # Fallback to default prefix
        return self._default_prefix

    async def _persist_prefix(self, guild_id: int, prefix: str) -> None:
        """Persist a prefix change to the database.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID
        prefix : str
            The prefix to persist
        """
        try:
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; prefix change not persisted")
                return

            # Ensure guild exists
            await controller.guild.get_or_create_guild(guild_id)

            # Update guild config
            await controller.guild_config.update_config(guild_id, prefix=prefix)

            logger.debug(f"Prefix persisted for guild {guild_id}: '{prefix}'")

        except Exception as e:
            logger.error(f"Failed to persist prefix for guild {guild_id}: {type(e).__name__}")
            # Remove from cache if persistence failed to maintain consistency
            self._prefix_cache.pop(guild_id, None)

    async def load_all_prefixes(self) -> None:
        """Load all guild prefixes into cache at startup.

        This is called once during bot initialization to populate the cache
        with all existing guild configurations.
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

                # Load all guild configs with timeout to prevent blocking
                logger.debug("Loading all guild prefixes into cache...")
                all_configs = await asyncio.wait_for(
                    controller.guild_config.find_all(limit=1000),  # Limit to prevent loading too many
                    timeout=10.0,  # 10 second timeout
                )

                for config in all_configs:
                    if hasattr(config, "guild_id") and hasattr(config, "prefix"):
                        self._prefix_cache[config.guild_id] = config.prefix

                self._cache_loaded = True
                logger.info(f"Loaded {len(self._prefix_cache)} guild prefixes into cache")

            except TimeoutError:
                logger.warning("Timeout loading prefix cache - continuing without cache")
                self._cache_loaded = True  # Mark as loaded to prevent retries
            except Exception as e:
                logger.error(f"Failed to load prefix cache: {type(e).__name__}")
                self._cache_loaded = True  # Mark as loaded to prevent retries

    def invalidate_cache(self, guild_id: int | None = None) -> None:
        """Invalidate prefix cache for a specific guild or all guilds.

        Parameters
        ----------
        guild_id : int | None, optional
            The guild ID to invalidate, or None to invalidate all, by default None
        """
        if guild_id is None:
            self._prefix_cache.clear()
            self._cache_loaded = False
            logger.debug("All prefix cache invalidated")
        else:
            self._prefix_cache.pop(guild_id, None)
            logger.debug(f"Prefix cache invalidated for guild {guild_id}")

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics for monitoring.

        Returns
        -------
        dict[str, int]
            Cache statistics including size and loaded status
        """
        return {
            "cached_prefixes": len(self._prefix_cache),
            "cache_loaded": int(self._cache_loaded),
        }
