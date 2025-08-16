from __future__ import annotations

from datetime import UTC, datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

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
	async def is_perm_afk(self, member_id: int, *, guild_id: int, session: AsyncSession) -> bool:
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
		session: AsyncSession,
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
		entry.nickname = nickname
		entry.reason = reason
		entry.guild_id = guild_id
		entry.perm_afk = is_perm
		entry.until = until
		entry.enforced = enforced
		await session.flush()
		await session.refresh(entry)
		return entry

	@with_session
	async def remove_afk(self, member_id: int, *, session: AsyncSession) -> bool:
		instance = await session.get(AFK, member_id)
		if instance is None:
			return False
		await session.delete(instance)
		await session.flush()
		return True

	@with_session
	async def get_all_afk_members(self, guild_id: int, *, session: AsyncSession) -> List[AFK]:
		stmt = select(AFK).where(AFK.guild_id == guild_id)
		res = await session.execute(stmt)
		return list(res.scalars())