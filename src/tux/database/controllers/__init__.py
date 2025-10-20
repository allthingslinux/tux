"""
Database Controllers for Tux Bot.

This module provides the controller layer for database operations,
offering lazy-loaded controllers for different data models and
coordinated access to database functionality.
"""

from __future__ import annotations

__all__ = [
    "AfkController",
    "BaseController",
    "CaseController",
    "DatabaseCoordinator",
    "GuildCommandPermissionController",
    "GuildConfigController",
    "GuildController",
    "GuildPermissionAssignmentController",
    "GuildPermissionRankController",
    "LevelsController",
    "ReminderController",
    "SnippetController",
    "StarboardController",
    "StarboardMessageController",
]

from tux.database.controllers.afk import AfkController
from tux.database.controllers.base import BaseController as BaseController  # Explicit re-export
from tux.database.controllers.case import CaseController
from tux.database.controllers.guild import GuildController
from tux.database.controllers.guild_config import GuildConfigController
from tux.database.controllers.guild_permissions import (
    GuildCommandPermissionController,
    GuildPermissionAssignmentController,
    GuildPermissionRankController,
)
from tux.database.controllers.levels import LevelsController
from tux.database.controllers.reminder import ReminderController
from tux.database.controllers.snippet import SnippetController
from tux.database.controllers.starboard import StarboardController, StarboardMessageController
from tux.database.service import DatabaseService


class DatabaseCoordinator:
    """Coordinator for database controllers with lazy loading.

    Provides centralized access to all database controllers with lazy initialization
    to avoid unnecessary resource allocation. Acts as a facade for database operations.

    Parameters
    ----------
    db : DatabaseService
        The database service instance to use for operations.

    Attributes
    ----------
    db : DatabaseService
        The underlying database service.

    Raises
    ------
    RuntimeError
        If no database service is provided.
    """

    def __init__(self, db: DatabaseService | None = None):
        """
        Initialize the database coordinator.

        Parameters
        ----------
        db : DatabaseService, optional
            The database service instance. If None, raises RuntimeError.

        Raises
        ------
        RuntimeError
            If no database service is provided.
        """
        if db is None:
            error_msg = "DatabaseService must be provided. Use DI container to get the service."
            raise RuntimeError(error_msg)
        self.db = db
        self._guild: GuildController | None = None
        self._guild_config: GuildConfigController | None = None
        self._guild_permissions: GuildPermissionRankController | None = None
        self._guild_permission_assignments: GuildPermissionAssignmentController | None = None
        self._guild_command_permissions: GuildCommandPermissionController | None = None
        self._afk: AfkController | None = None
        self._levels: LevelsController | None = None
        self._snippet: SnippetController | None = None
        self._case: CaseController | None = None
        self._starboard: StarboardController | None = None
        self._starboard_message: StarboardMessageController | None = None
        self._reminder: ReminderController | None = None

    @property
    def guild(self) -> GuildController:
        """Get the guild controller for guild-related operations."""
        if self._guild is None:
            self._guild = GuildController(self.db)
        return self._guild

    @property
    def guild_config(self) -> GuildConfigController:
        """Get the guild configuration controller."""
        if self._guild_config is None:
            self._guild_config = GuildConfigController(self.db)
        return self._guild_config

    @property
    def afk(self) -> AfkController:
        """Get the AFK status controller."""
        if self._afk is None:
            self._afk = AfkController(self.db)
        return self._afk

    @property
    def levels(self) -> LevelsController:
        """Get the user leveling controller."""
        if self._levels is None:
            self._levels = LevelsController(self.db)
        return self._levels

    @property
    def snippet(self) -> SnippetController:
        """Get the snippet controller for custom commands."""
        if self._snippet is None:
            self._snippet = SnippetController(self.db)
        return self._snippet

    @property
    def case(self) -> CaseController:
        """Get the moderation case controller."""
        if self._case is None:
            self._case = CaseController(self.db)
        return self._case

    @property
    def starboard(self) -> StarboardController:
        """Get the starboard configuration controller."""
        if self._starboard is None:
            self._starboard = StarboardController(self.db)
        return self._starboard

    @property
    def starboard_message(self) -> StarboardMessageController:
        """Get the starboard message controller."""
        if self._starboard_message is None:
            self._starboard_message = StarboardMessageController(self.db)
        return self._starboard_message

    @property
    def reminder(self) -> ReminderController:
        """Get the reminder controller."""
        if self._reminder is None:
            self._reminder = ReminderController(self.db)
        return self._reminder

    @property
    def guild_permissions(self) -> GuildPermissionRankController:
        """Get the guild permission ranks controller."""
        if self._guild_permissions is None:
            self._guild_permissions = GuildPermissionRankController(self.db)
        return self._guild_permissions

    @property
    def permission_assignments(self) -> GuildPermissionAssignmentController:
        """Get the permission assignments controller."""
        if self._guild_permission_assignments is None:
            self._guild_permission_assignments = GuildPermissionAssignmentController(self.db)
        return self._guild_permission_assignments

    @property
    def command_permissions(self) -> GuildCommandPermissionController:
        """Get the command permissions controller."""
        if self._guild_command_permissions is None:
            self._guild_command_permissions = GuildCommandPermissionController(self.db)
        return self._guild_command_permissions
