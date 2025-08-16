from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.services.database import DatabaseService


F = TypeVar("F", bound=Callable[..., Awaitable[Any]])


def with_session(func: F) -> F:
    @wraps(func)
    async def wrapper(self: "BaseController", *args: Any, **kwargs: Any):
        async with self.db.session() as session:
            return await func(self, *args, session=session, **kwargs)

    return wrapper  # type: ignore[return-value]


class BaseController:
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()