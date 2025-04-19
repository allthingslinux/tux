import asyncio
import signal
from types import FrameType
from typing import cast

import discord
import sentry_sdk
from loguru import logger
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from tux import __version__ as app_version
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.help import TuxHelp
from tux.utils.config import CONFIG
from tux.utils.env import get_current_env
from tux.utils.sentry import span as sentry_span
from tux.utils.sentry import start_span
from tux.utils.sentry import transaction as sentry_transaction


@sentry_span("bot.get_prefix", description="Resolving command prefix")
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
        List of valid prefixes for the message

    Notes
    -----
    If getting the guild prefix fails, falls back to the default prefix.
    """

    prefix: str | None = None

    if message.guild:
        try:
            prefix = await DatabaseController().guild_config.get_guild_prefix(message.guild.id)
        except Exception as e:
            logger.error(f"Error getting guild prefix: {e}")

    return [prefix or CONFIG.DEFAULT_PREFIX]


def setup_sentry() -> None:
    """Initialize Sentry with proper configuration.

    Notes
    -----
    Configures Sentry with:
    - Environment based on the current environment
    - Full tracing and profiling
    - Asyncio and Loguru integrations

    If no Sentry DSN is configured, logs a warning and skips setup.
    """
    if not CONFIG.SENTRY_DSN:
        logger.warning("No Sentry DSN configured, skipping Sentry setup")
        return

    logger.info("Setting up Sentry...")

    try:
        sentry_sdk.init(
            dsn=CONFIG.SENTRY_DSN,
            release=app_version,
            environment=get_current_env(),
            enable_tracing=True,
            attach_stacktrace=True,
            send_default_pii=False,
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


def add_transaction_context() -> None:
    """Add initial context tags to the Sentry transaction.

    This creates basic context for monitoring the bot lifecycle.
    """
    if sentry_sdk.is_initialized():
        current_transaction = sentry_sdk.get_current_span()

        if current_transaction is not None:
            current_transaction.set_tag("bot.version", app_version)
            current_transaction.set_tag("environment", get_current_env())


def validate_configuration() -> bool:
    """Validate that all required configuration is present.

    Returns
    -------
    bool
        True if configuration is valid, False otherwise
    """
    if not CONFIG.BOT_TOKEN:
        if sentry_sdk.is_initialized():
            current_transaction = sentry_sdk.get_current_span()

            if current_transaction is not None:
                current_transaction.set_status("invalid_argument")
                current_transaction.set_data("error", "Missing bot token")

        logger.critical("No bot token provided. Set DEV_BOT_TOKEN or PROD_BOT_TOKEN in your .env file.")
        return False
    return True


def setup_signal_handlers() -> None:
    """Set up handlers for system signals.

    Configures signal handlers for graceful shutdown.
    """
    signal.signal(cast(int, signal.SIGTERM), handle_sigterm)
    signal.signal(cast(int, signal.SIGINT), handle_sigterm)


def initialize_bot() -> Tux:
    """Initialize the bot instance with all required configuration.

    Returns
    -------
    Tux
        The configured bot instance ready for connection
    """
    bot = Tux(
        command_prefix=get_prefix,
        strip_after_prefix=True,
        case_insensitive=True,
        intents=discord.Intents.all(),
        owner_ids={CONFIG.BOT_OWNER_ID, *CONFIG.SYSADMIN_IDS},
        allowed_mentions=discord.AllowedMentions(everyone=False),
        help_command=TuxHelp(),
    )

    if sentry_sdk.is_initialized():
        current_span = sentry_sdk.get_current_span()

        if current_span is not None:
            current_span.set_tag("bot.owner_count", len({CONFIG.BOT_OWNER_ID, *CONFIG.SYSADMIN_IDS}))
            current_span.set_tag("bot.has_intents_all", True)

    return bot


def log_startup_error(error_type: str, error: Exception | None = None) -> None:
    """Log startup errors with appropriate context and severity.

    Parameters
    ----------
    error_type : str
        The type of error that occurred (used for tagging)
    error : Optional[Exception]
        The exception that occurred, if any
    """
    if sentry_sdk.is_initialized():
        current_span = sentry_sdk.get_current_span()

        if current_span is not None:
            if error_type == "keyboard_interrupt":
                current_span.set_tag("shutdown.reason", "keyboard_interrupt")
                logger.info("Initiating shutdown...")

            elif error_type == "login_failure":
                current_span.set_status("unauthenticated")
                current_span.set_tag("shutdown.reason", "login_failure")
                logger.critical("Failed to login. Check your token.")

            elif error_type == "intents_required":
                current_span.set_status("permission_denied")
                current_span.set_tag("shutdown.reason", "intents_not_enabled")
                logger.critical("Privileged intents are required but not enabled in the Discord Developer Portal.")

            elif error_type == "unexpected":
                current_span.set_status("internal_error")
                current_span.set_tag("shutdown.reason", "unexpected_error")
                if error:
                    current_span.set_data("error", str(error))
                    logger.critical(f"Unexpected error during startup: {error}")
                    sentry_sdk.capture_exception(error)


async def shutdown_bot(bot: Tux) -> None:
    """Perform graceful shutdown of the bot.

    Parameters
    ----------
    bot : Tux
        The bot instance to shut down
    """
    try:
        if not bot.is_closed():
            await bot.shutdown()

    except Exception as e:
        sentry_sdk.capture_exception(e)
        logger.error(f"Error during shutdown: {e}")

    if sentry_sdk.is_initialized():
        # Calculate approximate uptime if available
        if hasattr(bot, "start_time") and bot.start_time:
            uptime = asyncio.get_event_loop().time() - bot.start_time
            current_span = sentry_sdk.get_current_span()

            if current_span is not None:
                current_span.set_data("bot.uptime_seconds", uptime)

        sentry_sdk.flush()
        await asyncio.sleep(0.1)

    logger.info("Shutdown complete")


@sentry_transaction("bot.lifecycle", name="Bot Lifecycle", description="Complete bot startup to shutdown cycle")
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
    # Add initial context tags
    add_transaction_context()

    # Validate configuration early to avoid unnecessary work
    if not validate_configuration():
        return

    # Sentry setup phase
    with start_span("bot.setup_sentry", "Initialize Sentry monitoring"):
        setup_sentry()

    # Signal handler setup
    with start_span("bot.setup_signals", "Set up signal handlers"):
        setup_signal_handlers()

    # Bot initialization phase
    with start_span("bot.initialize", "Initialize bot instance"):
        bot = initialize_bot()

    try:
        # Bot startup phase
        with start_span("bot.start", "Connect and start the bot"):
            await bot.start(CONFIG.BOT_TOKEN, reconnect=True)

    except KeyboardInterrupt:
        log_startup_error("keyboard_interrupt")
    except discord.LoginFailure:
        log_startup_error("login_failure")
    except discord.PrivilegedIntentsRequired:
        log_startup_error("intents_required")
    except Exception as e:
        log_startup_error("unexpected", e)

    finally:
        # Shutdown phase
        with start_span("bot.shutdown", "Perform graceful shutdown"):
            await shutdown_bot(bot)


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
