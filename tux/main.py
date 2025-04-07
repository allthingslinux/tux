import asyncio
import signal
from types import FrameType
from typing import cast

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.help import TuxHelp
from tux.utils.config import CONFIG
from tux.utils.env import get_current_env


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Get the command prefix for a guild or default prefix.

    Parameters
    ----------
    bot : Tux
        The bot instance
    message : discord.Message
        The message to get the prefix for

    Returns
    -------
    list[str]
        List of valid prefixes for the message, including mentions

    Notes
    -----
    If getting the guild prefix fails, falls back to the default prefix.
    Always includes bot mention as a valid prefix.
    """

    prefix: str | None = None

    if message.guild:
        try:
            prefix = await DatabaseController().guild_config.get_guild_prefix(message.guild.id)
        except Exception as e:
            logger.error(f"Error getting guild prefix: {e}")

    return commands.when_mentioned_or(prefix or CONFIG.DEFAULT_PREFIX)(bot, message)


def setup_sentry() -> None:
    """Initialize Sentry with proper configuration.

    Notes
    -----
    Configures Sentry with:
    - Environment based on CONFIG.DEV
    - Full tracing and profiling
    - Asyncio and Loguru integrations

    If no Sentry URL is configured, logs a warning and skips setup.
    """
    if not CONFIG.SENTRY_URL:
        logger.warning("No Sentry URL configured, skipping Sentry setup")
        return

    logger.info("Setting up Sentry...")

    try:
        sentry_sdk.init(
            dsn=CONFIG.SENTRY_URL,
            environment=get_current_env(),
            enable_tracing=True,
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            integrations=[
                AsyncioIntegration(),
                LoggingIntegration(),
            ],
        )

        logger.info(f"Sentry initialized: {sentry_sdk.is_initialized()}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def handle_sigterm(signum: int, frame: FrameType | None) -> None:
    """Handle SIGTERM by raising KeyboardInterrupt.

    Parameters
    ----------
    signum : int
        Signal number received
    frame : FrameType | None
        Current stack frame

    Notes
    -----
    This handler converts SIGTERM into a KeyboardInterrupt to trigger
    graceful shutdown through the same path as Ctrl+C.
    """

    logger.info(f"Received signal {signum}")
    raise KeyboardInterrupt


async def main() -> None:
    """Main entry point for the bot.

    This function handles the complete lifecycle of the bot:
    1. Configuration validation
    2. Sentry setup
    3. Signal handlers
    4. Bot initialization and startup
    5. Error handling
    6. Graceful shutdown

    Raises
    ------
    discord.LoginFailure
        If the bot token is invalid
    discord.PrivilegedIntentsRequired
        If required intents are not enabled
    KeyboardInterrupt
        If shutdown is triggered by signal or Ctrl+C

    Notes
    -----
    The function ensures proper cleanup in all cases:
    - Graceful bot shutdown
    - Sentry cleanup
    - Final logging
    """

    if not CONFIG.BOT_TOKEN:
        logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
        return

    setup_sentry()

    # Set up signal handlers early
    signal.signal(cast(int, signal.SIGTERM), handle_sigterm)
    signal.signal(cast(int, signal.SIGINT), handle_sigterm)

    bot = Tux(
        command_prefix=get_prefix,
        strip_after_prefix=True,
        case_insensitive=True,
        intents=discord.Intents.all(),
        owner_ids={CONFIG.BOT_OWNER_ID, *CONFIG.SYSADMIN_IDS},
        allowed_mentions=discord.AllowedMentions(everyone=False),
        help_command=TuxHelp(),
    )

    try:
        await bot.start(CONFIG.BOT_TOKEN, reconnect=True)

    except KeyboardInterrupt:
        logger.info("Initiating shutdown...")
    except discord.LoginFailure:
        logger.critical("Failed to login. Check your token.")
    except discord.PrivilegedIntentsRequired:
        logger.critical("Privileged intents are required but not enabled in the Discord Developer Portal.")
    except Exception as e:
        logger.critical(f"Unexpected error during startup: {e}")
        sentry_sdk.capture_exception(e)

    finally:
        try:
            if not bot.is_closed():
                await bot.shutdown()

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        if sentry_sdk.is_initialized():
            sentry_sdk.flush()
            await asyncio.sleep(0.1)

        logger.info("Shutdown complete")


def run() -> int:
    """Entry point for the bot.

    This function serves as the main entry point when running the bot through the CLI.
    It wraps the async main() function in asyncio.run().

    Returns
    -------
    int
        Exit code (0 for success, non-zero for failure)
    """

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Exiting")
    return 0
