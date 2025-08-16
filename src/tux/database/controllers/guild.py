from __future__ import annotations

from typing import Any

from sqlmodel import select

from tux.database.controllers.base import BaseController
from tux.database.models.guild import Guild, GuildConfig


class GuildController(BaseController):
    async def get_guild_by_id(self, guild_id: int) -> Guild | None:
        async with self.db.session() as session:
            return await session.get(Guild, guild_id)

    async def get_or_create_guild(self, guild_id: int) -> Guild:
        async with self.db.session() as session:
            guild = await session.get(Guild, guild_id)
            if guild is not None:
                return guild
            return await Guild.create(session, guild_id=guild_id)

    async def insert_guild_by_id(self, guild_id: int) -> Guild:
        async with self.db.session() as session:
            return await Guild.create(session, guild_id=guild_id)

    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        async with self.db.session() as session:
            return await session.get(GuildConfig, guild_id)

    async def update_guild_config(self, guild_id: int, data: dict[str, Any]) -> GuildConfig:
        async with self.db.session() as session:
            config = await session.get(GuildConfig, guild_id)
            if config is None:
                return await GuildConfig.create(session, guild_id=guild_id, **data)
            for k, v in data.items():
                setattr(config, k, v)
            await session.flush()
            await session.refresh(config)
            return config