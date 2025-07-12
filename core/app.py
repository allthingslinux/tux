"""TuxApp: Orchestration and lifecycle management for the Tux Discord bot."""

import asyncio
import signal
from types import FrameType

import discord
import sentry_sdk
from loguru import logger

from core.bot import Tux
from core.config import CONFIG
from core.env import get_current_env
from core.help import TuxHelp


async def get_prefix(bot: Tux, message: discord.Message) -> list[str]:
    """Resolve the command prefix for a guild or use the default prefix."""
    prefix: str | None = None
    if message.guild:
        try:
            from infra.database.controllers import DatabaseController  # noqa: PLC0415

            prefix = await DatabaseController().guild_config.get_guild_prefix(message.guild.id)
        except Exception as e:
            logger.error(f"Error getting guild prefix: {e}")
    return [prefix or CONFIG.DEFAULT_PREFIX]


class TuxApp:
    """Orchestrates the startup, shutdown, and environment for the Tux bot."""

    def __init__(self):
        """Initialize the TuxApp with no bot instance yet."""
        self.bot = None

    def run(self) -> None:
        """Run the Tux bot application (entrypoint for CLI)."""
        asyncio.run(self.start())

    def setup_sentry(self) -> None:
        """Initialize Sentry for error monitoring and tracing."""
        if not CONFIG.SENTRY_DSN:
            logger.warning("No Sentry DSN configured, skipping Sentry setup")
            return

        logger.info("Setting up Sentry...")

        try:
            sentry_sdk.init(
                dsn=CONFIG.SENTRY_DSN,
                release=CONFIG.BOT_VERSION,
                environment=get_current_env(),
                enable_tracing=True,
                attach_stacktrace=True,
                send_default_pii=False,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                _experiments={
                    "enable_logs": True,  # https://docs.sentry.io/platforms/python/logs/
                },
            )

            # Add additional global tags
            sentry_sdk.set_tag("discord_library_version", discord.__version__)

            logger.info(f"Sentry initialized: {sentry_sdk.is_initialized()}")

        except Exception as e:
            logger.error(f"Failed to initialize Sentry: {e}")

    def setup_signals(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        signal.signal(signal.SIGINT, self.handle_sigterm)

    def handle_sigterm(self, signum: int, frame: FrameType | None) -> None:
        """Handle SIGTERM/SIGINT by raising KeyboardInterrupt for graceful shutdown."""
        logger.info(f"Received signal {signum}")

        if sentry_sdk.is_initialized():
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("signal.number", signum)
                scope.set_tag("lifecycle.event", "termination_signal")

                sentry_sdk.add_breadcrumb(
                    category="lifecycle",
                    message=f"Received termination signal {signum}",
                    level="info",
                )

        raise KeyboardInterrupt

    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        if not CONFIG.BOT_TOKEN:
            logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
            return False

        return True

    async def start(self) -> None:
        """Start the Tux bot, handling setup, errors, and shutdown."""
        self.setup_sentry()

        self.setup_signals()

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
            # owner_ids={CONFIG.BOT_OWNER_ID, *CONFIG.SYSADMIN_IDS},
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

        if sentry_sdk.is_initialized():
            sentry_sdk.flush()
            await asyncio.sleep(0.1)

        logger.info("Shutdown complete")
