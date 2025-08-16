from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, List, Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController, with_session
from tux.database.models.moderation import Case, CaseType


class CaseController(BaseController):
	@with_session
	async def insert_case(
		self,
		*,
		guild_id: int,
		case_user_id: int,
		case_moderator_id: int,
		case_type: CaseType,
		case_reason: str,
		case_expires_at: datetime | None = None,
		session: AsyncSession,
	) -> Case:
		# Determine next case number scoped to guild
		stmt = select(Case.case_number).where(Case.guild_id == guild_id).order_by(desc(Case.case_number)).limit(1)
		res = await session.execute(stmt)
		next_num = (res.scalar_one_or_none() or 0) + 1
		return await Case.create(
			session,
			guild_id=guild_id,
			case_user_id=case_user_id,
			case_moderator_id=case_moderator_id,
			case_type=case_type,
			case_reason=case_reason,
			case_number=next_num,
			case_expires_at=case_expires_at,
		)

	@with_session
	async def get_latest_case_by_user(self, guild_id: int, user_id: int, *, session: AsyncSession) -> Optional[Case]:
		stmt = (
			select(Case)
			.where(and_(Case.guild_id == guild_id, Case.case_user_id == user_id))
			.order_by(desc(Case.created_at))
			.limit(1)
		)
		res = await session.execute(stmt)
		return res.scalars().first()

	@with_session
	async def get_case_by_number(self, guild_id: int, case_number: int, *, session: AsyncSession) -> Optional[Case]:
		stmt = select(Case).where(and_(Case.guild_id == guild_id, Case.case_number == case_number)).limit(1)
		res = await session.execute(stmt)
		return res.scalars().first()

	@with_session
	async def get_cases_by_options(self, guild_id: int, options: dict[str, Any], *, session: AsyncSession) -> List[Case]:
		conditions: list[Any] = [Case.guild_id == guild_id]
		for key, value in options.items():
			conditions.append(getattr(Case, key) == value)
		stmt = select(Case).where(and_(*conditions)).order_by(desc(Case.created_at))
		res = await session.execute(stmt)
		return list(res.scalars())

	@with_session
	async def get_all_cases(self, guild_id: int, *, session: AsyncSession) -> List[Case]:
		stmt = select(Case).where(Case.guild_id == guild_id).order_by(desc(Case.created_at))
		res = await session.execute(stmt)
		return list(res.scalars())

	@with_session
	async def update_case(
		self,
		guild_id: int,
		case_number: int,
		*,
		case_reason: str | None = None,
		case_status: bool | None = None,
		session: AsyncSession,
	) -> Optional[Case]:
		case = await self.get_case_by_number(guild_id, case_number, session=session)
		if case is None:
			return None
		if case_reason is not None:
			case.case_reason = case_reason
		if case_status is not None:
			case.case_status = case_status
		await session.flush()
		await session.refresh(case)
		return case

	@with_session
	async def set_tempban_expired(self, case_id: int, guild_id: int, *, session: AsyncSession) -> bool:
		case = await session.get(Case, case_id)
		if case is None or case.guild_id != guild_id:
			return False
		case.case_status = False
		await session.flush()
		return True

	@with_session
	async def get_expired_tempbans(self, *, session: AsyncSession) -> List[Case]:
		# any expired and still active TEMPBAN cases
		stmt = select(Case).where(
			and_(Case.case_type == CaseType.TEMPBAN, Case.case_status == True, Case.case_expires_at <= datetime.now(UTC))
		)
		res = await session.execute(stmt)
		return list(res.scalars())

	@with_session
	async def is_user_under_restriction(
		self,
		*,
		guild_id: int,
		user_id: int,
		active_restriction_type: CaseType,
		inactive_restriction_type: CaseType,
		session: AsyncSession,
	) -> bool:
		stmt = (
			select(Case)
			.where(and_(Case.guild_id == guild_id, Case.case_user_id == user_id))
			.order_by(desc(Case.created_at))
			.limit(1)
		)
		res = await session.execute(stmt)
		latest = res.scalars().first()
		if latest is None:
			return False
		if latest.case_type == inactive_restriction_type:
			return False
		if latest.case_type == active_restriction_type and (latest.case_status is True):
			return True
		return False