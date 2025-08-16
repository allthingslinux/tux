from __future__ import annotations

from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar
from typing_extensions import Concatenate, ParamSpec

from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.services.database import DatabaseService


P = ParamSpec("P")
R = TypeVar("R")


def with_session(
    func: Callable[Concatenate["BaseController", P], Awaitable[R]]
) -> Callable[Concatenate["BaseController", P], Awaitable[R]]:
    @wraps(func)
    async def wrapper(self: "BaseController", *args: P.args, **kwargs: P.kwargs) -> R:
        if kwargs.get("session") is not None:
            return await func(self, *args, **kwargs)
        async with self.db.session() as session:
            return await func(self, *args, session=session, **kwargs)

    return wrapper


class BaseController:
    def __init__(self, db: DatabaseService | None = None):
        self.db = db or DatabaseService()
