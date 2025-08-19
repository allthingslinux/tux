from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlmodel import select

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.social import AFK


class AfkController(BaseController):
    @with_session
    async def get_afk_member(self, member_id: int, *, guild_id: int, session: Any = None) -> AFK | None:
        return await session.get(AFK, member_id)

    @with_session
    async def is_afk(self, member_id: int, *, guild_id: int, session: Any = None) -> bool:
        entry = await session.get(AFK, member_id)
        return entry is not None and entry.guild_id == guild_id

    @with_session
    async def is_perm_afk(self, member_id: int, *, guild_id: int, session: Any = None) -> bool:
        entry = await session.get(AFK, member_id)
        return bool(entry and entry.guild_id == guild_id and entry.perm_afk)

    @with_session
    async def set_afk(
        self,
        member_id: int,
        nickname: str,
        reason: str,
        guild_id: int,
        is_perm: bool,
        until: datetime | None = None,
        enforced: bool = False,
        *,
        session: Any = None,
    ) -> AFK:
        entry = await session.get(AFK, member_id)
        if entry is None:
            return await AFK.create(
                session,
                member_id=member_id,
                nickname=nickname,
                reason=reason,
                guild_id=guild_id,
                perm_afk=is_perm,
                until=until,
                enforced=enforced,
                since=datetime.now(UTC),
            )

        # Use the existing BaseModel update method
        updated_entry = await AFK.update_by_id(
            session,
            member_id,
            nickname=nickname,
            reason=reason,
            guild_id=guild_id,
            perm_afk=is_perm,
            until=until,
            enforced=enforced,
        )
        # This should never be None since we already checked entry exists above
        assert updated_entry is not None
        return updated_entry

    @with_session
    async def remove_afk(self, member_id: int, *, session: Any = None) -> bool:
        instance = await session.get(AFK, member_id)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True

    @with_session
    async def get_all_afk_members(self, guild_id: int, *, session: Any = None) -> list[AFK]:
        stmt = select(AFK).where(AFK.guild_id == guild_id)
        res = await session.execute(stmt)
        return list(res.scalars())

    @with_session
    async def find_many(self, *, where: dict[str, Any], session: Any = None) -> list[AFK]:
        stmt = select(AFK)
        for key, value in where.items():
            stmt = stmt.where(getattr(AFK, key) == value)
        res = await session.execute(stmt)
        return list(res.scalars())
