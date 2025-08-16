from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.guild import Guild, GuildConfig


class GuildController(BaseController):
    @with_session
    async def get_guild_by_id(self, guild_id: int, *, session: AsyncSession) -> Guild | None:
        return await session.get(Guild, guild_id)

    @with_session
    async def get_or_create_guild(self, guild_id: int, *, session: AsyncSession) -> Guild:
        guild = await session.get(Guild, guild_id)
        if guild is not None:
            return guild
        return await Guild.create(session, guild_id=guild_id)

    @with_session
    async def insert_guild_by_id(self, guild_id: int, *, session: AsyncSession) -> Guild:
        return await Guild.create(session, guild_id=guild_id)

    @with_session
    async def get_guild_config(self, guild_id: int, *, session: AsyncSession) -> GuildConfig | None:
        return await session.get(GuildConfig, guild_id)

    @with_session
    async def update_guild_config(self, guild_id: int, data: dict[str, Any], *, session: AsyncSession) -> GuildConfig:
        config = await session.get(GuildConfig, guild_id)
        if config is None:
            return await GuildConfig.create(session, guild_id=guild_id, **data)
        for k, v in data.items():
            setattr(config, k, v)
        await session.flush()
        await session.refresh(config)
        return config
