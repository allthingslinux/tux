from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, TypeVar

from tux.database.services import CacheService
from tux.database.services.database import DatabaseService

R = TypeVar("R")


def with_session(
    func: Callable[..., Awaitable[R]],
) -> Callable[..., Awaitable[R]]:
    @wraps(func)
    async def wrapper(self: BaseController, *args: Any, **kwargs: Any) -> R:
        if kwargs.get("session") is not None:
            return await func(self, *args, **kwargs)
        async with self.db.session() as session:
            return await func(self, *args, session=session, **kwargs)

    return wrapper


class BaseController:
    def __init__(self, db: DatabaseService | None = None, cache: CacheService | None = None):
        self.db = db or DatabaseService()
        self.cache = cache
