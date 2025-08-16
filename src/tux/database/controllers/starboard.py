from __future__ import annotations

from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.starboard import Starboard, StarboardMessage


class StarboardController(BaseController):
	@with_session
	async def create_or_update_starboard(
		self,
		guild_id: int,
		*,
		starboard_channel_id: int,
		starboard_emoji: str,
		starboard_threshold: int,
		session: AsyncSession,
	) -> Starboard:
		inst = await session.get(Starboard, guild_id)
		if inst is None:
			return await Starboard.create(
				session,
				guild_id=guild_id,
				starboard_channel_id=starboard_channel_id,
				starboard_emoji=starboard_emoji,
				starboard_threshold=starboard_threshold,
			)
		inst.starboard_channel_id = starboard_channel_id
		inst.starboard_emoji = starboard_emoji
		inst.starboard_threshold = starboard_threshold
		await session.flush()
		await session.refresh(inst)
		return inst

	@with_session
	async def delete_starboard_by_guild_id(self, guild_id: int, *, session: AsyncSession) -> bool:
		inst = await session.get(Starboard, guild_id)
		if inst is None:
			return False
		await session.delete(inst)
		await session.flush()
		return True

	@with_session
	async def get_starboard_by_guild_id(self, guild_id: int, *, session: AsyncSession) -> Optional[Starboard]:
		return await session.get(Starboard, guild_id)


class StarboardMessageController(BaseController):
	@with_session
	async def get_starboard_message_by_id(self, message_id: int, *, session: AsyncSession) -> Optional[StarboardMessage]:
		return await session.get(StarboardMessage, message_id)

	@with_session
	async def create_or_update_starboard_message(
		self,
		*,
		message_id: int,
		message_channel_id: int,
		message_user_id: int,
		message_guild_id: int,
		message_content: str,
		star_count: int,
		starboard_message_id: int,
		session: AsyncSession,
	) -> StarboardMessage:
		inst = await session.get(StarboardMessage, message_id)
		if inst is None:
			return await StarboardMessage.create(
				session,
				message_id=message_id,
				message_channel_id=message_channel_id,
				message_user_id=message_user_id,
				message_guild_id=message_guild_id,
				message_content=message_content,
				star_count=star_count,
				starboard_message_id=starboard_message_id,
			)
		inst.message_channel_id = message_channel_id
		inst.message_user_id = message_user_id
		inst.message_guild_id = message_guild_id
		inst.message_content = message_content
		inst.star_count = star_count
		inst.starboard_message_id = starboard_message_id
		await session.flush()
		await session.refresh(inst)
		return inst