"""Transaction management for database controllers."""

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from tux.database.service import DatabaseService

ModelT = TypeVar("ModelT", bound=SQLModel)
R = TypeVar("R")


class TransactionController[ModelT]:
    """Handles transaction and session management."""

    def __init__(self, model: type[ModelT], db: DatabaseService):
        self.model = model
        self.db = db

    async def with_session[R](self, operation: Callable[[AsyncSession], Awaitable[R]]) -> R:
        """Execute operation within a session context."""
        async with self.db.session() as session:
            return await operation(session)

    async def with_transaction[R](self, operation: Callable[[AsyncSession], Awaitable[R]]) -> R:
        """Execute operation within a transaction context."""
        async with self.db.session() as session, session.begin():
            return await operation(session)

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute a callback within a transaction."""
        async with self.db.session() as session, session.begin():
            return await callback()

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
        """Safely get attribute from object."""
        try:
            return getattr(obj, attr, default)
        except (AttributeError, TypeError):
            return default
