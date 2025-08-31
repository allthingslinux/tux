"""Tux application entrypoint and lifecycle utilities.

This module provides the orchestration necessary to run the Tux Discord bot,
including:

- Command prefix resolution based on per-guild configuration
- Signal handling for graceful shutdown
- Validation of runtime configuration
- Structured startup/shutdown flow with Sentry integration
"""

import asyncio
import contextlib
import signal
import sys
from types import FrameType

import discord
from loguru import logger

from tux.core.bot import Tux
from tux.database.utils import get_db_controller_from
from tux.help import TuxHelp
from tux.services.sentry_manager import SentryManager
from tux.shared.config import CONFIG


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Get the command prefix for a guild.

    This function retrieves the guild-specific prefix from the database,
    falling back to `CONFIG.get_prefix()` when the guild is unavailable or the database
    cannot be resolved.
    """
    if not message.guild:
        return [CONFIG.get_prefix()]

    prefix: str | None = None

    try:
        controller = get_db_controller_from(bot, fallback_to_direct=False)
        if controller is None:
            logger.warning("Database unavailable; using default prefix")
        else:
            # Ensure the guild exists in the database first
            await controller.guild.get_or_create_guild(message.guild.id)

            # Get or create guild config with default prefix
            guild_config = await controller.guild_config.get_or_create_config(
                message.guild.id,
                prefix=CONFIG.get_prefix(),  # Use the default prefix as the default value
            )
            if guild_config and hasattr(guild_config, "prefix"):
                prefix = guild_config.prefix

    except Exception as e:
        logger.error(f"❌ Error getting guild prefix: {type(e).__name__}")
        logger.info("💡 Using default prefix due to database or configuration error")

    return [prefix or CONFIG.get_prefix()]


class TuxApp:
    """Application wrapper that manages Tux bot lifecycle.

    This class encapsulates setup, run, and shutdown phases of the bot,
    providing consistent signal handling and configuration validation.
    """

    def __init__(self):
        """Initialize the application state.

        Notes
        -----
        The bot instance is not created until :meth:`start` to ensure the
        event loop and configuration are ready.
        """
        self.bot: Tux | None = None

    def run(self) -> None:
        """Run the Tux bot application.

        This is the synchronous entrypoint typically invoked by the CLI.
        """
        asyncio.run(self.start())

    def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """Register signal handlers for graceful shutdown.

        Parameters
        ----------
        loop : asyncio.AbstractEventLoop
            The active event loop on which to register handlers.

        Notes
        -----
        Uses ``loop.add_signal_handler`` where available, falling back to the
        ``signal`` module on platforms that do not support it (e.g. Windows).
        """

        def _sigterm() -> None:
            SentryManager.report_signal(signal.SIGTERM, None)
            # Trigger graceful shutdown by closing the bot
            if hasattr(self, "bot") and self.bot and not self.bot.is_closed():
                # Schedule the close operation in the event loop
                bot = self.bot  # Type narrowing
                with contextlib.suppress(Exception):
                    loop.call_soon_threadsafe(lambda: asyncio.create_task(bot.close()))

        def _sigint() -> None:
            SentryManager.report_signal(signal.SIGINT, None)
            # Trigger graceful shutdown by closing the bot
            if hasattr(self, "bot") and self.bot and not self.bot.is_closed():
                # Schedule the close operation in the event loop
                bot = self.bot  # Type narrowing
                with contextlib.suppress(Exception):
                    loop.call_soon_threadsafe(lambda: asyncio.create_task(bot.close()))

        try:
            loop.add_signal_handler(signal.SIGTERM, _sigterm)
            loop.add_signal_handler(signal.SIGINT, _sigint)

        except NotImplementedError:
            # Fallback for platforms that do not support add_signal_handler (e.g., Windows)
            def _signal_handler(signum: int, frame: FrameType | None) -> None:
                SentryManager.report_signal(signum, frame)
                # For Windows fallback, just log the signal

            signal.signal(signal.SIGTERM, _signal_handler)
            signal.signal(signal.SIGINT, _signal_handler)

        if sys.platform.startswith("win"):
            logger.warning(
                "Warning: Signal handling is limited on Windows. Some signals may not be handled as expected.",
            )

    async def start(self) -> None:
        """Start the Tux bot, managing setup and error handling.

        This method initializes Sentry, registers signal handlers, validates
        configuration, constructs the bot, and begins the Discord connection.
        """

        # Initialize Sentry via façade
        SentryManager.setup()

        # Setup signals via event loop
        loop = asyncio.get_running_loop()
        self.setup_signals(loop)

        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set BOT_TOKEN in your .env file.")
            sys.exit(1)

        owner_ids = {CONFIG.USER_IDS.BOT_OWNER_ID}

        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning(
                "⚠️ Eval is enabled for sysadmins, this is potentially dangerous; see .env file for more info.",
            )
            owner_ids.update(CONFIG.USER_IDS.SYSADMINS)
        else:
            logger.warning("🔒️ Eval is disabled for sysadmins; see .env file for more info.")

        self.bot = Tux(
            command_prefix=get_prefix,
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_ids=owner_ids,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            help_command=TuxHelp(),
            activity=None,
            status=discord.Status.online,
        )

        try:
            # Start the bot normally - this handles login() + connect() properly
            await self.bot.start(CONFIG.BOT_TOKEN, reconnect=True)
        except asyncio.CancelledError:
            # Handle cancellation gracefully
            logger.info("Bot startup was cancelled")
        except KeyboardInterrupt:
            logger.info("Shutdown requested (KeyboardInterrupt)")
        except Exception as e:
            logger.critical(f"❌ Bot failed to start: {type(e).__name__}")
            logger.info("💡 Check your configuration and ensure all services are properly set up")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and flush telemetry.

        Ensures the bot client is closed and Sentry is flushed asynchronously
        before returning.
        """

        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        await SentryManager.flush_async()

        logger.info("Shutdown complete")
