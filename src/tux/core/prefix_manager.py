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


class PrefixManager:
    """
    Manages command prefixes with in-memory caching for optimal performance.

    This class provides:
    - In-memory cache of guild prefixes
    - Lazy loading from database
    - Event-driven cache updates
    - Graceful fallback to default prefix
    - Zero database hits per message after initial load

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

    Notes
    -----
    Prefix resolution follows this priority:
    1. Environment variable override (BOT_INFO__PREFIX)
    2. In-memory cache (O(1) lookup)
    3. Database lookup with automatic caching
    4. Default prefix fallback
    """

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the prefix manager with empty cache.

        Parameters
        ----------
        bot : Tux
            The bot instance to manage prefixes for.
        """
        self.bot = bot

        # In-memory cache for fast prefix lookups (guild_id -> prefix)
        self._prefix_cache: dict[int, str] = {}

        # Track whether we've performed the initial cache load
        self._cache_loaded = False

        # Default prefix from configuration (fallback)
        self._default_prefix = CONFIG.get_prefix()

        # Lock to prevent race conditions during initial cache load
        self._loading_lock = asyncio.Lock()

        logger.debug("PrefixManager initialized")

    # ---------- Public API ----------

    async def get_prefix(self, guild_id: int) -> str:
        """
        Get the command prefix for a guild with automatic caching.

        Resolution order:
        1. Check for environment variable override
        2. Check in-memory cache (O(1))
        3. Load from database and cache
        4. Fallback to default prefix

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        str
            The command prefix for the guild, or default prefix if not found.

        Notes
        -----
        This method is called on every message, so it's optimized for speed.
        After initial cache load, this is an O(1) dictionary lookup.
        """
        # Priority 1: Check if prefix override is enabled by environment variable
        # This allows forcing a specific prefix across all guilds for testing
        if CONFIG.is_prefix_override_enabled():
            logger.debug(f"Prefix override enabled, using default prefix '{self._default_prefix}' for guild {guild_id}")
            return self._default_prefix

        # Priority 2: Check cache first (fast path - O(1) lookup)
        if guild_id in self._prefix_cache:
            return self._prefix_cache[guild_id]

        # Priority 3: Cache miss - load from database and cache result
        return await self._load_guild_prefix(guild_id)

    async def set_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Set the command prefix for a guild with immediate cache update.

        The cache is updated immediately for instant effect, while database
        persistence happens asynchronously to avoid blocking command execution.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The new command prefix to set.

        Notes
        -----
        If prefix override is enabled via environment variable, this method
        will log a warning but won't update the prefix (override takes priority).
        """
        # Check if prefix override is enabled - warn but don't update
        # This prevents confusion when BOT_INFO__PREFIX is set
        if CONFIG.is_prefix_override_enabled():
            logger.warning(
                f"Prefix override enabled - ignoring prefix change for guild {guild_id} to '{prefix}'. All guilds use default prefix '{self._default_prefix}'",
            )
            return

        # Update cache immediately for instant effect
        self._prefix_cache[guild_id] = prefix

        # Persist to database asynchronously (don't block command execution)
        # Create task but don't await - persistence happens in background
        persist_task = asyncio.create_task(self._persist_prefix(guild_id, prefix))

        # Store reference to prevent garbage collection before task completes
        # Python will GC tasks that have no references, even if they're running
        _ = persist_task

        logger.info(f"Prefix updated for guild {guild_id}: '{prefix}'")

    # ---------- Private Database Operations ----------

    async def _load_guild_prefix(self, guild_id: int) -> str:
        """
        Load a guild's prefix from the database and cache it.

        This method is called on cache misses. It ensures the guild exists
        in the database, loads or creates its config, and caches the result.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.

        Returns
        -------
        str
            The guild's prefix, or default prefix if loading fails.

        Notes
        -----
        This method always returns a prefix - it never raises. Database
        errors are logged and the default prefix is returned as fallback.
        """
        try:
            # Get database controller (without fallback to avoid blocking)
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; using default prefix")
                return self._default_prefix

            # Ensure guild record exists in database
            await controller.guild.get_or_create_guild(guild_id)

            # Get or create guild config with default prefix
            guild_config = await controller.guild_config.get_or_create_config(
                guild_id,
                prefix=self._default_prefix,
            )

            # Extract prefix from config and cache it
            if guild_config and hasattr(guild_config, "prefix"):
                prefix = guild_config.prefix
                self._prefix_cache[guild_id] = prefix  # Cache for future lookups
                return prefix

        except Exception as e:
            # Log error but don't crash - prefix resolution must always succeed
            logger.warning(f"Failed to load prefix for guild {guild_id}: {type(e).__name__}")

        # Fallback to default prefix if any step fails
        return self._default_prefix

    async def _persist_prefix(self, guild_id: int, prefix: str) -> None:
        """
        Persist a prefix change to the database asynchronously.

        This method runs in the background after set_prefix updates the cache.
        If persistence fails, the cache entry is removed to maintain consistency
        between cache and database.

        Parameters
        ----------
        guild_id : int
            The Discord guild ID.
        prefix : str
            The prefix to persist.

        Notes
        -----
        This method is called as a background task and never raises. Failures
        are logged and the cache is rolled back to maintain data consistency.
        """
        try:
            # Get database controller
            controller = get_db_controller_from(self.bot, fallback_to_direct=False)
            if controller is None:
                logger.warning("Database unavailable; prefix change not persisted")
                return

            # Ensure guild record exists
            await controller.guild.get_or_create_guild(guild_id)

            # Update guild config with new prefix
            await controller.guild_config.update_config(guild_id, prefix=prefix)

            logger.debug(f"Prefix persisted for guild {guild_id}: '{prefix}'")

        except Exception as e:
            logger.error(f"Failed to persist prefix for guild {guild_id}: {type(e).__name__}")

            # IMPORTANT: Remove from cache if persistence failed
            # This maintains consistency - we don't want a prefix in cache
            # that doesn't exist in the database (could cause issues on restart)
            self._prefix_cache.pop(guild_id, None)

    # ---------- Cache Management ----------

    async def load_all_prefixes(self) -> None:
        """
        Load all guild prefixes into cache at startup.

        This method is called once during bot initialization to populate the
        cache with all existing guild configurations from the database. It uses
        a lock to prevent concurrent loading and has built-in timeout protection.

        Notes
        -----
        - Uses a lock to prevent duplicate loads if called concurrently
        - Has a 10-second timeout to prevent blocking startup
        - Loads up to 1000 guild configs (should be more than enough)
        - Marks cache as loaded even on failure to prevent retry loops
        - Idempotent - safe to call multiple times
        """
        # Quick check before acquiring lock (fast path)
        if self._cache_loaded:
            return

        # Acquire lock to prevent concurrent loading
        async with self._loading_lock:
            # Check again after acquiring lock (double-check pattern)
            if self._cache_loaded:
                return

            try:
                # Get database controller
                controller = get_db_controller_from(self.bot, fallback_to_direct=False)
                if controller is None:
                    logger.warning("Database unavailable; prefix cache not loaded")
                    self._cache_loaded = True  # Mark as loaded to prevent retries
                    return

                # Load all guild configs with timeout to prevent blocking startup
                logger.debug("Loading all guild prefixes into cache...")
                all_configs = await asyncio.wait_for(
                    controller.guild_config.find_all(limit=1000),  # Limit for safety
                    timeout=10.0,  # Don't block startup for more than 10 seconds
                )

                # Populate cache with loaded configs
                for config in all_configs:
                    if hasattr(config, "guild_id") and hasattr(config, "prefix"):
                        self._prefix_cache[config.guild_id] = config.prefix

                self._cache_loaded = True
                logger.info(f"Loaded {len(self._prefix_cache)} guild prefixes into cache")

            except TimeoutError:
                # Timeout is not fatal - bot can still work with empty cache
                logger.warning("Timeout loading prefix cache - continuing without cache")
                self._cache_loaded = True  # Mark as loaded to prevent retries

            except Exception as e:
                # Other errors are also not fatal - mark as loaded to prevent retries
                logger.error(f"Failed to load prefix cache: {type(e).__name__}")
                self._cache_loaded = True  # Prevent retry loops

    def invalidate_cache(self, guild_id: int | None = None) -> None:
        """
        Invalidate prefix cache for a specific guild or all guilds.

        This is useful when guild configs are updated externally or when
        you need to force a reload from the database.

        Parameters
        ----------
        guild_id : int | None, optional
            The guild ID to invalidate, or None to invalidate all.
            Defaults to None (invalidate all).

        Examples
        --------
        Invalidate a specific guild:
        >>> manager.invalidate_cache(123456789)

        Invalidate entire cache:
        >>> manager.invalidate_cache()
        """
        if guild_id is None:
            # Clear entire cache and reset loaded flag
            self._prefix_cache.clear()
            self._cache_loaded = False
            logger.debug("All prefix cache invalidated")
        else:
            # Remove specific guild from cache
            self._prefix_cache.pop(guild_id, None)
            logger.debug(f"Prefix cache invalidated for guild {guild_id}")

    def get_cache_stats(self) -> dict[str, int]:
        """
        Get cache statistics for monitoring and debugging.

        Returns
        -------
        dict[str, int]
            Dictionary containing:
            - cached_prefixes: Number of guilds in cache
            - cache_loaded: 1 if initial load completed, 0 otherwise

        Examples
        --------
        >>> stats = manager.get_cache_stats()
        >>> print(f"Cached: {stats['cached_prefixes']} guilds")
        Cached: 42 guilds
        """
        return {
            "cached_prefixes": len(self._prefix_cache),
            "cache_loaded": int(self._cache_loaded),
        }
