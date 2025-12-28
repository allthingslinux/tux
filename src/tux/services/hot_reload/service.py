"""Main hot reload service implementation."""

import asyncio
import time
from typing import TYPE_CHECKING, Any

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger

from tux.services.sentry import capture_exception_safe
from tux.services.sentry.tracing import span

from .config import HotReloadConfig, ModuleReloadError, validate_config
from .dependencies import ClassDefinitionTracker, DependencyGraph
from .file_utils import FileHashTracker
from .watcher import FileWatcher

if TYPE_CHECKING:
    from tux.core.bot import Tux


class HotReload(commands.Cog):
    """Enhanced hot reload system with dependency tracking and performance monitoring."""

    def __init__(self, bot: "Tux", config: HotReloadConfig | None = None) -> None:
        """
        Initialize the hot reload service.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        config : HotReloadConfig | None, optional
            Hot reload configuration, by default None.
        """
        self.bot = bot
        self.config = config or HotReloadConfig()

        # Validate configuration
        validate_config(self.config)

        # Initialize components
        self.file_watcher: FileWatcher | None = None
        self.hash_tracker = FileHashTracker()
        self.dependency_graph = DependencyGraph(
            max_depth=self.config.max_dependency_depth,
        )
        self.class_tracker = ClassDefinitionTracker()

        # Performance monitoring
        self._reload_stats = {
            "total_reloads": 0,
            "successful_reloads": 0,
            "failed_reloads": 0,
            "average_reload_time": 0.0,
        }

        # State
        self._is_enabled = self.config.enabled
        self._reload_lock = asyncio.Lock()
        self._pending_reloads: dict[str, asyncio.Task[None]] = {}

    async def cog_load(self) -> None:
        """Initialize the hot reload system when cog is loaded."""
        if self._is_enabled:
            await self.start_watching()

    async def cog_unload(self) -> None:
        """Clean up when cog is unloaded."""
        await self.stop_watching()

    async def start_watching(self) -> None:
        """Start file system watching."""
        if self.file_watcher is not None:
            logger.warning("Hot reload already watching")
            return

        try:
            self.file_watcher = FileWatcher(self.config, self._handle_file_change)
            self.file_watcher.start()
            logger.info("Hot reload system started")
        except Exception as e:
            logger.error(f"Failed to start hot reload: {e}")
            capture_exception_safe(e)

    async def stop_watching(self) -> None:
        """Stop file system watching."""
        if self.file_watcher is None:
            return

        try:
            self.file_watcher.stop()
            self.file_watcher = None
            logger.info("Hot reload system stopped")
        except Exception as e:
            logger.error(f"Failed to stop hot reload: {e}")
            capture_exception_safe(e)

    def _handle_file_change(self, extension: str) -> None:
        """Handle file change events."""
        logger.info(f"📁 Hot reload: File change detected for extension {extension}")
        if not self._is_enabled:
            logger.warning("Hot reload: System disabled, ignoring file change")
            return

        # Schedule async reload with debouncing
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                return  # Don't reload if loop is closed

            # Check if we already have a pending reload for this extension
            if extension in self._pending_reloads:
                # Cancel existing timer and create new one
                self._pending_reloads[extension].cancel()

            # Create debounced reload
            async def debounced_reload():
                """
                Execute debounced reload after delay.

                This coroutine waits for the debounce period before executing the
                reload to avoid multiple rapid reloads of the same extension.
                """
                await asyncio.sleep(self.config.debounce_delay)
                if extension in self._pending_reloads:
                    del self._pending_reloads[extension]
                logger.info(f"Hot reload: Executing debounced reload for {extension}")
                await self._reload_extension_async(extension)

            # Schedule the debounced reload
            task = loop.create_task(debounced_reload())
            self._pending_reloads[extension] = task
            logger.info(f"Hot reload: Scheduled debounced reload for {extension}")

        except RuntimeError:
            # No event loop running, skip reload during shutdown
            logger.warning("Hot reload: No event loop available, skipping reload")
            return

    async def _reload_extension_async(self, extension: str) -> None:
        """Asynchronously reload an extension."""
        logger.info(f"Hot reload: Starting reload of {extension}")
        async with self._reload_lock:
            await self._reload_extension_with_monitoring(extension)

    @span("hot_reload.reload_extension")
    async def _reload_extension_with_monitoring(self, extension: str) -> None:
        """Reload extension with performance monitoring."""
        start_time = time.time()
        self._reload_stats["total_reloads"] += 1

        try:
            # Use push_scope for isolated scope to avoid polluting current scope
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("extension", extension)
                scope.set_tag("reload_type", "hot_reload")

            success = await self._perform_reload(extension)

            if success:
                self._reload_stats["successful_reloads"] += 1
                logger.success(f"Successfully reloaded {extension}")
            else:
                self._reload_stats["failed_reloads"] += 1
                logger.error(f"Failed to reload {extension}")

        except Exception as e:
            self._reload_stats["failed_reloads"] += 1
            logger.error(f"Error reloading {extension}: {e}")
            capture_exception_safe(e)

        finally:
            # Update performance stats
            reload_time = time.time() - start_time
            total_reloads = self._reload_stats["total_reloads"]
            current_avg = self._reload_stats["average_reload_time"]
            self._reload_stats["average_reload_time"] = (
                current_avg * (total_reloads - 1) + reload_time
            ) / total_reloads

    async def _perform_reload(self, extension: str) -> bool:
        """
        Perform the actual extension reload.

        Returns
        -------
        bool
            True if reload was successful, False otherwise.

        Raises
        ------
        ModuleReloadError
            If reload fails and continue_on_error is False.
        """
        try:
            # Check if extension is loaded
            if extension not in self.bot.extensions:
                logger.info(f"Extension {extension} not loaded, attempting to load")
                await self.bot.load_extension(extension)
                return True

            # Reload the extension
            await self.bot.reload_extension(extension)

        except commands.ExtensionNotLoaded:
            logger.warning(f"Extension {extension} not loaded, attempting to load")
            try:
                await self.bot.load_extension(extension)
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
                return False
            else:
                return True

        except Exception as e:
            logger.error(f"Failed to reload extension {extension}: {e}")
            if not self.config.continue_on_error:
                msg = f"Failed to reload {extension}"
                raise ModuleReloadError(msg) from e
            return False
        else:
            return True

    @commands.group(name="hotreload", aliases=["hr"])
    @commands.is_owner()
    async def hotreload_group(self, ctx: commands.Context[Any]) -> None:
        """Hot reload management commands."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @hotreload_group.command(name="status")
    async def status(self, ctx: commands.Context[Any]) -> None:
        """Show hot reload system status."""
        status = "🟢 Enabled" if self._is_enabled else "🔴 Disabled"
        watching = (
            "🟢 Active"
            if self.file_watcher and self.file_watcher.is_running()
            else "🔴 Inactive"
        )

        stats = self._reload_stats
        embed = discord.Embed(
            title="Hot Reload Status",
            color=0x00FF00 if self._is_enabled else 0xFF0000,
        )
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="File Watching", value=watching, inline=True)
        embed.add_field(name="Total Reloads", value=stats["total_reloads"], inline=True)
        embed.add_field(
            name="Successful",
            value=stats["successful_reloads"],
            inline=True,
        )
        embed.add_field(name="Failed", value=stats["failed_reloads"], inline=True)
        embed.add_field(
            name="Avg Time",
            value=f"{stats['average_reload_time']:.2f}s",
            inline=True,
        )

        await ctx.send(embed=embed)

    @hotreload_group.command(name="enable")
    async def enable(self, ctx: commands.Context[Any]) -> None:
        """Enable hot reload system."""
        if self._is_enabled:
            await ctx.send("Hot reload is already enabled.")
            return

        self._is_enabled = True
        await self.start_watching()
        await ctx.send("✅ Hot reload system enabled.")

    @hotreload_group.command(name="disable")
    async def disable(self, ctx: commands.Context[Any]) -> None:
        """Disable hot reload system."""
        if not self._is_enabled:
            await ctx.send("Hot reload is already disabled.")
            return

        self._is_enabled = False
        await self.stop_watching()
        await ctx.send("🔴 Hot reload system disabled.")

    @hotreload_group.command(name="reload")
    async def manual_reload(self, ctx: commands.Context[Any], extension: str) -> None:
        """Manually reload an extension."""
        async with ctx.typing():
            success = await self._perform_reload(extension)
            if success:
                await ctx.send(f"✅ Successfully reloaded {extension}")
            else:
                await ctx.send(f"❌ Failed to reload {extension}")

    @property
    def is_enabled(self) -> bool:
        """Check if hot reload is enabled."""
        return self._is_enabled

    @property
    def reload_stats(self) -> dict[str, Any]:
        """Get reload statistics."""
        return self._reload_stats.copy()
