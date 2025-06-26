"""
TuxApp: Main application entrypoint and lifecycle orchestrator.

This module contains the `TuxApp` class, which serves as the primary entrypoint
for the Tux Discord bot. It is responsible for:

- **Environment Setup**: Validating configuration, initializing Sentry, and setting
  up OS-level signal handlers for graceful shutdown.
- **Bot Instantiation**: Creating the instance of the `Tux` bot class with the
  appropriate intents, command prefix logic, and owner IDs.
- **Lifecycle Management**: Starting the asyncio event loop and managing the
  bot's main `start` and `shutdown` sequence, including handling `KeyboardInterrupt`.
"""

import asyncio
import signal

import discord
from loguru import logger

from tux.bot import Tux
from tux.help import TuxHelp
from tux.utils.config import CONFIG
from tux.utils.sentry_manager import SentryManager


class TuxApp:
    """
    Orchestrates the startup, shutdown, and environment for the Tux bot.

    This class is not a `discord.py` cog, but rather a top-level application
    runner that manages the bot's entire lifecycle from an OS perspective.
    """

    # --- Initialization ---

    def __init__(self):
        """Initializes the TuxApp, setting the bot instance to None initially."""
        self.bot: Tux | None = None

    # --- Application Lifecycle ---

    def run(self) -> None:
        """
        The main synchronous entrypoint for the application.

        This method starts the asyncio event loop and runs the primary `start`
        coroutine, effectively launching the bot.
        """
        asyncio.run(self.start())

    async def start(self) -> None:
        """
        The main asynchronous entrypoint for the application.

        This method orchestrates the entire bot startup sequence: setting up
        Sentry and signal handlers, validating config, creating the `Tux`
        instance, and connecting to Discord. It includes a robust
        try/except/finally block to ensure graceful shutdown.
        """

        # Initialize Sentry
        SentryManager.setup()

        # Set up signal handlers
        self.setup_signals()

        # Validate config
        if not self.validate_config():
            return

        # Configure owner IDs, dynamically adding sysadmins if configured.
        # This allows specified users to have access to sensitive commands like `eval`.
        owner_ids = {CONFIG.BOT_OWNER_ID}
        if CONFIG.ALLOW_SYSADMINS_EVAL:
            logger.warning(
                "⚠️ Eval is enabled for sysadmins, this is potentially dangerous; "
                "see settings.yml.example for more info.",
            )
            owner_ids.update(CONFIG.SYSADMIN_IDS)
        else:
            logger.warning("🔒️ Eval is disabled for sysadmins; see settings.yml.example for more info.")

        # Instantiate the main bot class with all necessary parameters.
        self.bot = Tux(
            strip_after_prefix=True,
            case_insensitive=True,
            intents=discord.Intents.all(),
            owner_ids=owner_ids,
            allowed_mentions=discord.AllowedMentions(everyone=False),
            help_command=TuxHelp(),
            activity=None,
            status=discord.Status.online,
        )

        # Start the bot
        try:
            # This is the main blocking call that connects to Discord and runs the bot.
            await self.bot.start(CONFIG.BOT_TOKEN, reconnect=True)

        except KeyboardInterrupt:
            # This is caught when the user presses Ctrl+C.
            logger.info("Shutdown requested (KeyboardInterrupt)")
        except Exception as e:
            # Catch any other unexpected exception during bot runtime.
            logger.critical(f"Bot failed to start or run: {e}")
        finally:
            # Ensure that shutdown is always called to clean up resources.
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shuts down the bot and its resources.

        This involves calling the bot's internal shutdown sequence and then
        flushing any remaining Sentry events to ensure all data is sent.
        """
        if self.bot and not self.bot.is_closed():
            await self.bot.shutdown()

        SentryManager.flush()
        await asyncio.sleep(0.1)  # Brief pause to allow buffers to flush

        logger.info("Shutdown complete")

    # --- Environment Setup ---

    def setup_signals(self) -> None:
        """
        Sets up OS-level signal handlers for graceful shutdown.

        This ensures that when the bot process receives a SIGINT (Ctrl+C) or
        SIGTERM (from systemd or Docker), it is intercepted and handled
        cleanly instead of causing an abrupt exit.
        """
        signal.signal(signal.SIGTERM, SentryManager.report_signal)
        signal.signal(signal.SIGINT, SentryManager.report_signal)

    def validate_config(self) -> bool:
        """
        Performs a pre-flight check for essential configuration.

        Returns
        -------
        bool
            True if the configuration is valid, False otherwise.
        """
        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
            return False

        return True
