"""Main entry point for Tux bot."""

# Initialize logging first, before any other imports that might log
import asyncio
import signal
from types import FrameType

import discord
import sentry_sdk
from discord.ext import commands
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.loguru import LoguruIntegration

from tux.bot import Tux
from tux.database.controllers.guild_config import GuildConfigController
from tux.help import TuxHelp
from tux.utils.config import CONFIG
from tux.utils.logging import setup_logging

setup_logging()


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Get the command prefix for a guild or default prefix."""
    prefix: str | None = None

    if message.guild:
        try:
            prefix = await GuildConfigController().get_guild_prefix(message.guild.id)
        except Exception as e:
            logger.error(f"Error getting guild prefix: {e}")
            # Fall back to default prefix

    return commands.when_mentioned_or(prefix or CONFIG.DEFAULT_PREFIX)(bot, message)


def setup_sentry() -> None:
    """Initialize Sentry with proper configuration."""
    if not CONFIG.SENTRY_URL:
        logger.warning("No Sentry URL configured, skipping Sentry setup")
        return

    logger.info("Setting up Sentry...")

    try:
        sentry_sdk.init(
            dsn=CONFIG.SENTRY_URL,
            environment="dev" if CONFIG.DEV == "True" else "prod",
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
            enable_tracing=True,
            integrations=(AsyncioIntegration(), LoguruIntegration()),
        )
        logger.info(f"Sentry initialized: {sentry_sdk.is_initialized()}")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def handle_sigterm(signum: int, frame: FrameType | None) -> None:
    """Handle SIGTERM by raising KeyboardInterrupt."""
    logger.info(f"Received signal {signum}")
    raise KeyboardInterrupt


async def main() -> None:
    """Main entry point for the bot."""
    if not CONFIG.TOKEN:
        logger.critical("No token provided. Set TOKEN in your environment or .env file.")
        return

    setup_sentry()

    # Set up signal handlers early
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)

    intents = discord.Intents.all()
    allowed_mentions = discord.AllowedMentions(everyone=False)

    bot = Tux(
        command_prefix=get_prefix,
        strip_after_prefix=True,
        case_insensitive=True,
        intents=intents,
        owner_ids={CONFIG.BOT_OWNER_ID, *CONFIG.SYSADMIN_IDS},
        allowed_mentions=allowed_mentions,
        help_command=TuxHelp(),
    )

    try:
        # Start the bot without context manager to handle shutdown manually
        await bot.start(CONFIG.TOKEN)
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
        # Ensure bot is properly shut down
        try:
            if not bot.is_closed():
                await bot.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

        # Close Sentry client
        if sentry_sdk.is_initialized():
            sentry_sdk.flush()
            await asyncio.sleep(0.1)  # Give tasks a moment to finish logging

        logger.info("Shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # Already handled in main()
    finally:
        logger.info("Exiting")
