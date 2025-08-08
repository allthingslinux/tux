"""TuxApp: Orchestration and lifecycle management for the Tux Discord bot."""

import asyncio
import signal
import sys

import discord
from loguru import logger

from tux.core.bot import Tux
from tux.core.interfaces import IDatabaseService
from tux.help import TuxHelp
from tux.services.sentry_manager import SentryManager
from tux.shared.config.settings import CONFIG


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Resolve the command prefix for a guild or use the default prefix."""
    prefix: str | None = None
    if message.guild:
        try:
            container = getattr(bot, "container", None)
            if container is None:
                logger.error("Service container missing on bot; DI is required for prefix resolution")
            else:
                db_service = container.get_optional(IDatabaseService)
                if db_service is None:
                    logger.warning("IDatabaseService not available; using default prefix")
                else:
                    controller = db_service.get_controller()
                    prefix = await controller.guild_config.get_guild_prefix(message.guild.id)
        except Exception as e:
            logger.error(f"Error getting guild prefix: {e}")
    return [prefix or CONFIG.DEFAULT_PREFIX]


class TuxApp:
    """Orchestrates the startup, shutdown, and environment for the Tux bot."""

    def __init__(self):
        """Initialize the TuxApp with no bot instance yet."""
        self.bot: Tux | None = None

    def run(self) -> None:
        """Run the Tux bot application (entrypoint for CLI)."""
        asyncio.run(self.start())

    def setup_signals(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set up signal handlers for graceful shutdown."""

        # Prefer event-loop handlers for portability
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

    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
            return False
        return True

    async def start(self) -> None:
        """Start the Tux bot, handling setup, errors, and shutdown."""
        # Initialize Sentry via façade
        SentryManager.setup()

        # Setup signals via event loop
        loop = asyncio.get_event_loop()
        self.setup_signals(loop)

        if not self.validate_config():
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
            await self.shutdown()
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Gracefully shut down the bot and flush Sentry."""
        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        # Asynchronous flush
        await SentryManager.flush_async()

        logger.info("Shutdown complete")
