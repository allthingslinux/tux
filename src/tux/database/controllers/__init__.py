from __future__ import annotations

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
    def __init__(self, db: DatabaseService | None = None):
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
        if self._guild is None:
            self._guild = GuildController(self.db)
        return self._guild

    @property
    def guild_config(self) -> GuildConfigController:
        if self._guild_config is None:
            self._guild_config = GuildConfigController(self.db)
        return self._guild_config

    @property
    def afk(self) -> AfkController:
        if self._afk is None:
            self._afk = AfkController(self.db)
        return self._afk

    @property
    def levels(self) -> LevelsController:
        if self._levels is None:
            self._levels = LevelsController(self.db)
        return self._levels

    @property
    def snippet(self) -> SnippetController:
        if self._snippet is None:
            self._snippet = SnippetController(self.db)
        return self._snippet

    @property
    def case(self) -> CaseController:
        if self._case is None:
            self._case = CaseController(self.db)
        return self._case

    @property
    def starboard(self) -> StarboardController:
        if self._starboard is None:
            self._starboard = StarboardController(self.db)
        return self._starboard

    @property
    def starboard_message(self) -> StarboardMessageController:
        if self._starboard_message is None:
            self._starboard_message = StarboardMessageController(self.db)
        return self._starboard_message

    @property
    def reminder(self) -> ReminderController:
        if self._reminder is None:
            self._reminder = ReminderController(self.db)
        return self._reminder

    @property
    def guild_permissions(self) -> GuildPermissionRankController:
        if self._guild_permissions is None:
            self._guild_permissions = GuildPermissionRankController(self.db)
        return self._guild_permissions

    @property
    def permission_assignments(self) -> GuildPermissionAssignmentController:
        if self._guild_permission_assignments is None:
            self._guild_permission_assignments = GuildPermissionAssignmentController(self.db)
        return self._guild_permission_assignments

    @property
    def command_permissions(self) -> GuildCommandPermissionController:
        if self._guild_command_permissions is None:
            self._guild_command_permissions = GuildCommandPermissionController(self.db)
        return self._guild_command_permissions
