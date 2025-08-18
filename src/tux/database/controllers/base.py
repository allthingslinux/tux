from __future__ import annotations

from functools import wraps
from typing import Awaitable, Callable, TypeVar, Any

from tux.database.services.database import DatabaseService
from tux.database.services import CacheService


R = TypeVar("R")


def with_session(
	func: Callable[..., Awaitable[R]]
) -> Callable[..., Awaitable[R]]:
	@wraps(func)
	async def wrapper(self: "BaseController", *args: Any, **kwargs: Any) -> R:
		if kwargs.get("session") is not None:
			return await func(self, *args, **kwargs)
		async with self.db.session() as session:
			return await func(self, *args, session=session, **kwargs)  # type: ignore[call-arg]

	return wrapper


class BaseController:
	def __init__(self, db: DatabaseService | None = None, cache: CacheService | None = None):
		self.db = db or DatabaseService()
		self.cache = cache
