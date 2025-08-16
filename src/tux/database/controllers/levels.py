from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from sqlalchemy import and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.social import Levels


class LevelsController(BaseController):
    @with_session
    async def get_xp(self, member_id: int, guild_id: int, *, session: AsyncSession) -> float:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        return 0.0 if rec is None else rec.xp

    @with_session
    async def get_level(self, member_id: int, guild_id: int, *, session: AsyncSession) -> int:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        return 0 if rec is None else rec.level

    @with_session
    async def get_xp_and_level(self, member_id: int, guild_id: int, *, session: AsyncSession) -> Tuple[float, int]:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        return (0.0, 0) if rec is None else (rec.xp, rec.level)

    @with_session
    async def get_last_message_time(self, member_id: int, guild_id: int, *, session: AsyncSession) -> datetime | None:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        return None if rec is None else rec.last_message

    @with_session
    async def is_blacklisted(self, member_id: int, guild_id: int, *, session: AsyncSession) -> bool:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        return False if rec is None else rec.blacklisted

    @with_session
    async def update_xp_and_level(
        self,
        member_id: int,
        guild_id: int,
        *,
        xp: float,
        level: int,
        last_message: datetime | None = None,
        session: AsyncSession,
    ) -> Levels:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        if rec is None:
            return await Levels.create(
                session,
                member_id=member_id,
                guild_id=guild_id,
                xp=xp,
                level=level,
                last_message=last_message or datetime.now(timezone.utc),
            )
        rec.xp = xp
        rec.level = level
        rec.last_message = last_message or datetime.now(timezone.utc)
        await session.flush()
        await session.refresh(rec)
        return rec

    @with_session
    async def toggle_blacklist(self, member_id: int, guild_id: int, *, session: AsyncSession) -> bool:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        if rec is None:
            created = await Levels.create(session, member_id=member_id, guild_id=guild_id, xp=0.0, level=0, blacklisted=True)
            return created.blacklisted
        rec.blacklisted = not rec.blacklisted
        await session.flush()
        return rec.blacklisted

    @with_session
    async def reset_xp(self, member_id: int, guild_id: int, *, session: AsyncSession) -> Levels | None:
        rec = await session.get(Levels, {"member_id": member_id, "guild_id": guild_id})  # type: ignore[arg-type]
        if rec is None:
            return None
        rec.xp = 0.0
        rec.level = 0
        await session.flush()
        await session.refresh(rec)
        return rec

    @staticmethod
    def calculate_level(xp: float) -> int:
        # Keep same logic as before (sqrt-based progression)
        import math

        return math.floor(math.sqrt(xp / 100))