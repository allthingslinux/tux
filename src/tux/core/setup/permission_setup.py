"""Permission system setup service for bot initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from tux.core.permission_system import init_permission_system
from tux.core.setup.base import BotSetupService
from tux.database.controllers import DatabaseCoordinator

if TYPE_CHECKING:
    from tux.core.bot import Tux
    from tux.database.service import DatabaseService

__all__ = ["PermissionSetupService"]


class PermissionSetupService(BotSetupService):
    """Handles permission system initialization during bot setup."""

    def __init__(self, bot: Tux, db_service: DatabaseService) -> None:
        """Initialize the permission setup service.

        Parameters
        ----------
        bot : Tux
            The Discord bot instance to set up permissions for.
        db_service : DatabaseService
            The database service instance for storing permissions.
        """
        super().__init__(bot, "permissions")
        self.db_service = db_service

    async def setup(self) -> None:
        """Set up the permission system for command authorization."""
        logger.info("Initializing permission system...")

        db_coordinator = DatabaseCoordinator(self.db_service)
        init_permission_system(self.bot, db_coordinator)

        logger.success("Permission system initialized successfully")
