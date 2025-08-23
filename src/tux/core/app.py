"""Tux application entrypoint and lifecycle utilities.

This module provides the orchestration necessary to run the Tux Discord bot,
including:

- Command prefix resolution based on per-guild configuration
- Signal handling for graceful shutdown
- Validation of runtime configuration
- Structured startup/shutdown flow with Sentry integration
"""

import asyncio
import signal
import sys

import discord
from loguru import logger

from tux.core.bot import Tux
from tux.database.utils import get_db_controller_from
from tux.help import TuxHelp
from tux.services.sentry_manager import SentryManager
from tux.shared.config.settings import CONFIG


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Get the command prefix for a guild.

    This function retrieves the guild-specific prefix from the database,
    falling back to `CONFIG.DEFAULT_PREFIX` when the guild is unavailable or the database
    cannot be resolved.
    """
    if not message.guild:
        return [CONFIG.DEFAULT_PREFIX]

    prefix: str | None = None

    try:
        controller = get_db_controller_from(bot, fallback_to_direct=False)
        if controller is None:
            logger.warning("Database unavailable; using default prefix")
        else:
            # Get guild config and extract prefix
            guild_config = await controller.guild_config.get_config_by_guild_id(message.guild.id)
            if guild_config and hasattr(guild_config, "prefix"):
                prefix = guild_config.prefix

    except Exception as e:
        logger.error(f"Error getting guild prefix: {e}")

    return [prefix or CONFIG.DEFAULT_PREFIX]


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

    @staticmethod
    def setup_signals(loop: asyncio.AbstractEventLoop) -> None:
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

        def _sigint() -> None:
            SentryManager.report_signal(signal.SIGINT, None)

        try:
            loop.add_signal_handler(signal.SIGTERM, _sigterm)
            loop.add_signal_handler(signal.SIGINT, _sigint)

        except NotImplementedError:
            # Fallback for platforms that do not support add_signal_handler (e.g., Windows)
            signal.signal(signal.SIGTERM, SentryManager.report_signal)
            signal.signal(signal.SIGINT, SentryManager.report_signal)

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
            logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
            return

        owner_ids = {CONFIG.BOT_OWNER_ID}

        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning(
                "⚠️ Eval is enabled for sysadmins, this is potentially dangerous; see settings.yml.example for more info.",
            )
            owner_ids.update(CONFIG.SYSADMIN_IDS)
        else:
            logger.warning("🔒️ Eval is disabled for sysadmins; see settings.yml.example for more info.")

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
            await self.bot.start(CONFIG.BOT_TOKEN, reconnect=True)
        except KeyboardInterrupt:
            logger.info("Shutdown requested (KeyboardInterrupt)")
        except Exception as e:
            logger.critical(f"Bot failed to start: {e}")
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
