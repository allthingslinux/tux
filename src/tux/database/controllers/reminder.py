from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.content import Reminder


class ReminderController(BaseController):
	@with_session
	async def insert_reminder(
		self,
		*,
		reminder_id: int,
		reminder_content: str,
		reminder_expires_at: datetime,
		reminder_channel_id: int,
		reminder_user_id: int,
		guild_id: int,
		session: AsyncSession,
	) -> Reminder:
		return await Reminder.create(
			session,
			reminder_id=reminder_id,
			reminder_content=reminder_content,
			reminder_expires_at=reminder_expires_at,
			reminder_channel_id=reminder_channel_id,
			reminder_user_id=reminder_user_id,
			guild_id=guild_id,
		)

	@with_session
	async def delete_reminder_by_id(self, reminder_id: int, *, session: AsyncSession) -> bool:
		inst = await session.get(Reminder, reminder_id)
		if inst is None:
			return False
		await session.delete(inst)
		await session.flush()
		return True

	@with_session
	async def get_reminder_by_id(self, reminder_id: int, *, session: AsyncSession) -> Optional[Reminder]:
		return await session.get(Reminder, reminder_id)

	@with_session
	async def get_all_reminders(self, guild_id: int, *, session: AsyncSession) -> List[Reminder]:
		stmt = select(Reminder).where(Reminder.guild_id == guild_id)
		res = await session.execute(stmt)
		return list(res.scalars())