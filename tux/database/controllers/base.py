from __future__ import annotations

"""Shared SQLModel-powered base controller replacing the old Prisma-based version."""

from collections.abc import Callable
from typing import Any, Generic, Type, TypeVar

import sentry_sdk
from loguru import logger
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from tux.database.client import db

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseController(Generic[ModelT]):
    """A thin asynchronous repository / DAO layer.

    The goal is *not* to hide SQLAlchemy entirely but to provide a small,
    opinionated convenience wrapper that matches the minimal subset of methods
    that were previously offered by the Prisma-powered controller.

    The public API therefore continues to expose familiar methods such as
    ``find_many`` or ``create`` so that the higher-level business-logic remains
    largely untouched.
    """

    def __init__(self, model: Type[ModelT]):
        self.model = model
        self.model_name = model.__name__.lower()
        # Backwards-compatibility – many controllers used `self.table` to access
        # the underlying ORM model (mainly for `.upsert`).
        self.table = model

    # ------------------------------------------------------------------
    # Helper – internal
    # ------------------------------------------------------------------

    async def _execute_query(self, op: Callable[[AsyncSession], Any], span_desc: str) -> Any:
        """Run *op* inside a managed session & sentry span (if enabled)."""

        if sentry_sdk.is_initialized():
            with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                span.set_tag("db.table", self.model_name)
                try:
                    async with db.session() as session:
                        result = await op(session)
                    span.set_status("ok")
                    return result  # noqa: TRY300 – maintain behaviour
                except Exception as exc:
                    span.set_status("internal_error")
                    span.set_data("error", str(exc))
                    logger.error(f"{span_desc}: {exc}")
                    raise
        else:
            async with db.session() as session:
                return await op(session)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    async def find_one(
        self,
        *,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,  # ignored but kept for API compatibility
        **__: Any,
    ) -> ModelT | None:  # noqa: D401 – simple
        """Return the first row that matches *where* or *None*."""

        async def _op(session: AsyncSession):  # noqa: D401 – nested
            stmt = select(self.model).filter_by(**where).limit(1)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(_op, f"find_one {self.model_name}")

    # NOTE: The old Prisma-powered layer had separate ``find_unique`` and
    # ``find_first`` helpers.  For our purposes a unique lookup is identical to
    # ``find_one`` when the *where* clause targets a unique / primary-key
    # constraint.

    async def find_unique(
        self,
        *,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,  # ignored
        **__: Any,
    ) -> ModelT | None:  # noqa: D401 – simple
        return await self.find_one(where=where, include=include)

    async def find_many(
        self,
        *,
        where: dict[str, Any] | None = None,
        order: dict[str, str] | None = None,
        take: int | None = None,
        skip: int | None = None,
    ) -> list[ModelT]:
        """Return a list of rows matching *where* (or all rows)."""

        async def _op(session: AsyncSession):
            stmt = select(self.model)
            if where:
                stmt = stmt.filter_by(**where)
            if order:
                # Expecting {"col": "asc"|"desc"}
                for col, direction in order.items():
                    column_attr = getattr(self.model, col)
                    stmt = stmt.order_by(column_attr.desc() if direction.lower() == "desc" else column_attr.asc())
            if take is not None:
                stmt = stmt.limit(take)
            if skip is not None:
                stmt = stmt.offset(skip)
            res = await session.execute(stmt)
            return res.scalars().all()

        return await self._execute_query(_op, f"find_many {self.model_name}")

    async def count(self, *, where: dict[str, Any] | None = None) -> int:
        async def _op(session: AsyncSession):
            stmt = select(func.count()).select_from(self.model)
            if where:
                stmt = stmt.filter_by(**where)
            result = await session.execute(stmt)
            return result.scalar_one()

        return await self._execute_query(_op, f"count {self.model_name}")

    async def create(self, *, data: dict[str, Any]) -> ModelT:
        async def _op(session: AsyncSession):
            obj = self.model(**data)  # type: ignore[arg-type]
            session.add(obj)
            await session.flush()  # populate PKs
            return obj

        return await self._execute_query(_op, f"create {self.model_name}")

    async def update(self, *, where: dict[str, Any], data: dict[str, Any]) -> ModelT | None:
        async def _op(session: AsyncSession):
            stmt = sa_update(self.model).filter_by(**where).values(**data).returning(self.model)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(_op, f"update {self.model_name}")

    async def delete(self, *, where: dict[str, Any]) -> ModelT | None:
        async def _op(session: AsyncSession):
            stmt = sa_delete(self.model).filter_by(**where).returning(self.model)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

        return await self._execute_query(_op, f"delete {self.model_name}")

    async def upsert(self, *, where: dict[str, Any], create: dict[str, Any], update: dict[str, Any]) -> ModelT:
        """Very naive *upsert* helper using a transaction (select → insert/update)."""

        async def _op(session: AsyncSession):
            stmt = select(self.model).filter_by(**where).with_for_update()
            result = await session.execute(stmt)
            obj = result.scalar_one_or_none()
            if obj is None:
                obj = self.model(**{**where, **create})  # type: ignore[arg-type]
                session.add(obj)
            else:
                for key, value in update.items():
                    setattr(obj, key, value)
            await session.flush()
            return obj

        return await self._execute_query(_op, f"upsert {self.model_name}")

    # ------------------------------------------------------------------
    # Utility helpers mirrored from old implementation
    # ------------------------------------------------------------------

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:  # noqa: D401 – util
        """Return ``getattr(obj, attr, default)`` – keeps old helper available."""
        return getattr(obj, attr, default)

    # The old implementation exposed a *static* connect_or_create_relation helper
    # used when inserting nested relations through Prisma.  Under SQLModel we can
    # just set the foreign-key field directly, but we keep this shim so that the
    # higher-level code does not need to be rewritten right away.
    @staticmethod
    def connect_or_create_relation(id_field: str, model_id: Any, *_: Any, **__: Any) -> dict[str, Any]:  # noqa: D401
        """Return a dict with a single key that can be merged into *data* dicts.

        The calling code does something like::

            data={
                "guild": connect_or_create_relation("guild_id", guild_id)
            }

        We map that pattern to a very small helper that collapses to `{"guild_id": guild_id}`.
        """
        return {id_field: model_id}
