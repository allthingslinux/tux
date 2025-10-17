"""Bot setup orchestrator that coordinates all setup services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.core.prefix_manager import PrefixManager
from tux.services.sentry.tracing import DummySpan, set_setup_phase_tag, start_span
from tux.shared.exceptions import TuxDatabaseConnectionError

if TYPE_CHECKING:
    from typing import Any

    from tux.core.bot import Tux


class BotSetupOrchestrator:
    """Orchestrates the bot setup process using specialized setup services."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the bot setup orchestrator.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance to set up.
        """
        self.bot = bot
        # Lazy import to avoid circular imports
        from .cog_setup import CogSetupService  # noqa: PLC0415
        from .database_setup import DatabaseSetupService  # noqa: PLC0415
        from .permission_setup import PermissionSetupService  # noqa: PLC0415

        self.database_setup = DatabaseSetupService(bot.db_service)
        self.permission_setup = PermissionSetupService(bot, bot.db_service)
        self.cog_setup = CogSetupService(bot)

    async def setup(self, span: DummySpan | Any) -> None:
        """Execute all setup steps with standardized error handling."""
        set_setup_phase_tag(span, "starting")

        # Database setup (includes migrations)
        if not await self.database_setup.safe_setup():
            msg = "Database setup failed"
            raise TuxDatabaseConnectionError(msg)
        set_setup_phase_tag(span, "database", "finished")

        # Permission system setup
        if not await self.permission_setup.safe_setup():
            msg = "Permission system setup failed"
            raise RuntimeError(msg)
        set_setup_phase_tag(span, "permissions", "finished")

        # Prefix manager setup
        await self._setup_prefix_manager(span)

        # Cog setup
        if not await self.cog_setup.safe_setup():
            msg = "Cog setup failed"
            raise RuntimeError(msg)
        set_setup_phase_tag(span, "cogs", "finished")

        # Start monitoring
        self.bot.task_monitor.start()
        set_setup_phase_tag(span, "monitoring", "finished")

    async def _setup_prefix_manager(self, span: DummySpan | Any) -> None:
        """Set up the prefix manager."""
        with start_span("bot.setup_prefix_manager", "Setting up prefix manager"):
            logger.info("🔧 Initializing prefix manager...")
            try:
                self.bot.prefix_manager = PrefixManager(self.bot)
                await self.bot.prefix_manager.load_all_prefixes()
                logger.info("✅ Prefix manager initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize prefix manager: {e}")
                logger.warning("⚠️  Bot will use default prefix for all guilds")
                self.bot.prefix_manager = None
        set_setup_phase_tag(span, "prefix_manager", "finished")
