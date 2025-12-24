"""Bot setup orchestrator that coordinates all setup services."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tux.services.sentry.tracing import DummySpan, set_setup_phase_tag
from tux.shared.exceptions import (
    TuxDatabaseConnectionError,
    TuxSetupError,
)

if TYPE_CHECKING:
    from typing import Any

    from tux.core.bot import Tux

__all__ = ["BotSetupOrchestrator"]


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
        from .prefix_setup import PrefixSetupService  # noqa: PLC0415

        self.services = [
            DatabaseSetupService(bot.db_service),
            PermissionSetupService(bot, bot.db_service),
            PrefixSetupService(bot),
            CogSetupService(bot),
        ]

    async def setup(self, span: DummySpan | Any) -> None:
        """
        Execute all setup steps with standardized error handling.

        Performs setup in order: database (with migrations), permission system,
        prefix manager, cogs, and task monitoring.

        Raises
        ------
        TuxDatabaseConnectionError
            If database setup fails.
        TuxSetupError
            If any setup service fails.
        """
        set_setup_phase_tag(span, "starting")

        for service in self.services:
            if not await service.safe_setup():
                # The underlying error is already logged and captured by safe_setup()
                msg = f"{service.name.title()} setup failed"

                if service.name == "database":
                    msg += (
                        ". Check logs and Sentry for the underlying error. "
                        "Common causes: database not running, incorrect connection "
                        "string, network issues, or migration failures. "
                        "Run migrations manually with 'uv run db push' if needed."
                    )
                    raise TuxDatabaseConnectionError(msg)

                raise TuxSetupError(msg)

            set_setup_phase_tag(span, service.name, "finished")

        # Start monitoring
        self.bot.task_monitor.start()
        set_setup_phase_tag(span, "monitoring", "finished")
