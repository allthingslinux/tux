from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.social import AFK


class AfkController(BaseController):
    @with_session
    async def get_afk_member(self, member_id: int, *, guild_id: int, session: AsyncSession) -> AFK | None:
        return await session.get(AFK, member_id)

    @with_session
    async def is_afk(self, member_id: int, *, guild_id: int, session: AsyncSession) -> bool:
        entry = await session.get(AFK, member_id)
        return entry is not None and entry.guild_id == guild_id

    @with_session
    async def remove_afk(self, member_id: int, *, session: AsyncSession) -> bool:
        instance = await session.get(AFK, member_id)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True