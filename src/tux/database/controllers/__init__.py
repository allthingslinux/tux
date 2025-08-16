from __future__ import annotations

from tux.database.controllers.guild import GuildController
from tux.database.services.database import DatabaseService


class DatabaseController:
    def __init__(self, db: DatabaseService | None = None) -> None:
        self.db = db or DatabaseService()
        self._guild: GuildController | None = None
        self._guild_config: GuildController | None = None

    @property
    def guild(self) -> GuildController:
        if self._guild is None:
            self._guild = GuildController(self.db)
        return self._guild

    @property
    def guild_config(self) -> GuildController:
        if self._guild_config is None:
            self._guild_config = GuildController(self.db)
        return self._guild_config