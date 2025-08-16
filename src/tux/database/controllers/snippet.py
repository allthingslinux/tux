from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy import func

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.content import Snippet


class SnippetController(BaseController):
	@with_session
	async def get_all_snippets_by_guild_id(self, guild_id: int, *, session: AsyncSession) -> List[Snippet]:
		stmt = select(Snippet).where(Snippet.guild_id == guild_id)
		res = await session.execute(stmt)
		return list(res.scalars())

	@with_session
	async def get_snippet_by_name_and_guild_id(
		self, snippet_name: str, guild_id: int, *, session: AsyncSession
	) -> Optional[Snippet]:
		stmt = select(Snippet).where((Snippet.guild_id == guild_id) & (func.lower(Snippet.snippet_name) == snippet_name.lower()))
		res = await session.execute(stmt)
		return res.scalars().first()

	@with_session
	async def create_snippet(
		self,
		snippet_name: str,
		snippet_content: str,
		snippet_created_at: datetime,
		snippet_user_id: int,
		guild_id: int,
		*,
		session: AsyncSession,
	) -> Snippet:
		return await Snippet.create(
			session,
			snippet_name=snippet_name,
			snippet_content=snippet_content,
			snippet_user_id=snippet_user_id,
			guild_id=guild_id,
			uses=0,
			locked=False,
			created_at=snippet_created_at or datetime.now(timezone.utc),
		)

	@with_session
	async def delete_snippet_by_id(self, snippet_id: int, *, session: AsyncSession) -> bool:
		inst = await session.get(Snippet, snippet_id)
		if inst is None:
			return False
		await session.delete(inst)
		await session.flush()
		return True

	@with_session
	async def update_snippet_by_id(self, snippet_id: int, snippet_content: str, *, session: AsyncSession) -> bool:
		inst = await session.get(Snippet, snippet_id)
		if inst is None:
			return False
		inst.snippet_content = snippet_content
		await session.flush()
		return True

	@with_session
	async def increment_snippet_uses(self, snippet_id: int, *, session: AsyncSession) -> bool:
		inst = await session.get(Snippet, snippet_id)
		if inst is None:
			return False
		inst.uses += 1
		await session.flush()
		return True

	@with_session
	async def toggle_snippet_lock_by_id(self, snippet_id: int, *, session: AsyncSession) -> Optional[Snippet]:
		inst = await session.get(Snippet, snippet_id)
		if inst is None:
			return None
		inst.locked = not inst.locked
		await session.flush()
		await session.refresh(inst)
		return inst

	@with_session
	async def create_snippet_alias(
		self,
		snippet_name: str,
		snippet_alias: str,
		snippet_created_at: datetime,
		snippet_user_id: int,
		guild_id: int,
		*,
		session: AsyncSession,
	) -> Snippet:
		return await Snippet.create(
			session,
			snippet_name=snippet_alias,
			alias=snippet_name,
			snippet_user_id=snippet_user_id,
			guild_id=guild_id,
			uses=0,
			locked=False,
			created_at=snippet_created_at or datetime.now(timezone.utc),
		)

	@with_session
	async def get_all_aliases(self, snippet_name: str, guild_id: int, *, session: AsyncSession) -> List[Snippet]:
		stmt = select(Snippet).where((func.lower(Snippet.alias) == snippet_name.lower()) & (Snippet.guild_id == guild_id))
		res = await session.execute(stmt)
		return list(res.scalars())