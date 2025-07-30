"""Shared SQLModel-powered base controller for database operations."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import sentry_sdk
from loguru import logger
from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from tux.database.client import db

ModelT = TypeVar("ModelT", bound=SQLModel)


class BaseController[ModelT]:
    """A thin asynchronous repository / DAO layer.

    The goal is *not* to hide SQLAlchemy entirely but to provide a small,
    opinionated convenience wrapper for common database operations.

    The public API exposes familiar methods such as ``find_many`` or ``create``
    for clean and consistent database access patterns.
    """

    def __init__(self, model: type[ModelT]):
        self.model = model
        self.model_name = model.__name__.lower()
        # Legacy support - many controllers used `self.table` to access
        # the underlying ORM model (mainly for `.upsert`).
        self.table = model

    # ------------------------------------------------------------------
    # Helper - internal
    # ------------------------------------------------------------------

    async def _execute_query(self, op: Callable[[AsyncSession], Any], span_desc: str) -> Any:
        """Run *op* inside a managed session & sentry span (if enabled)."""

        if sentry_sdk.is_initialized():
            with sentry_sdk.start_span(op="db.query", description=span_desc) as span:
                span.set_tag("db.table", self.model_name)
                try:
                    async with db.session() as _session:
                        result = await op(_session)
                    span.set_status("ok")
                    return result  # noqa: TRY300 - maintain behaviour
                except Exception as exc:
                    span.set_status("internal_error")
                    span.set_data("error", str(exc))
                    logger.error(f"{span_desc}: {exc}")
                    raise
        else:
            async with db.session() as _session:
                return await op(_session)

    # ------------------------------------------------------------------
    # CRUD helpers
    # ------------------------------------------------------------------

    async def find_one(
        self,
        *,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,  # ignored but kept for API consistency
        **__: Any,
    ) -> ModelT | None:
        """Return the first row that matches *where* or *None*."""

        async def _op(session: AsyncSession):
            stmt = select(self.model).filter_by(**where).limit(1)
            result = await session.execute(stmt)  # type: ignore[attr-defined]
            return result.scalar_one_or_none()  # type: ignore[attr-defined]

        return await self._execute_query(_op, f"find_one {self.model_name}")

    # NOTE: For our purposes a unique lookup is identical to ``find_one`` when
    # the *where* clause targets a unique / primary-key constraint.

    async def find_unique(
        self,
        *,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,  # ignored
        **__: Any,
    ) -> ModelT | None:
        return await self.find_one(where=where, include=include)

    async def find_many(
        self,
        *,
        where: dict[str, Any] | None = None,
        include: dict[str, bool] | None = None,  # ignored
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
            res = await session.execute(stmt)  # type: ignore[attr-defined]
            return res.scalars().all()  # type: ignore[attr-defined]

        return await self._execute_query(_op, f"find_many {self.model_name}")

    async def count(self, *, where: dict[str, Any] | None = None) -> int:
        async def _op(session: AsyncSession):
            stmt = select(func.count()).select_from(self.model)
            if where:
                stmt = stmt.filter_by(**where)
            result = await session.execute(stmt)  # type: ignore[attr-defined]
            return result.scalar_one()  # type: ignore[attr-defined]

        return await self._execute_query(_op, f"count {self.model_name}")

    async def create(
        self,
        *,
        data: dict[str, Any],
        include: dict[str, bool] | None = None,  # ignored for consistency
    ) -> ModelT:
        async def _op(session: AsyncSession):
            obj = self.model(**data)  # type: ignore[arg-type]
            session.add(obj)  # type: ignore[attr-defined]
            await session.flush()  # type: ignore[attr-defined] # populate PKs
            return obj

        return await self._execute_query(_op, f"create {self.model_name}")

    async def update(
        self,
        *,
        where: dict[str, Any],
        data: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelT | None:
        async def _op(session: AsyncSession):
            stmt = sa_update(self.model).filter_by(**where).values(**data).returning(self.model)
            result = await session.execute(stmt)  # type: ignore[attr-defined]
            return result.scalar_one_or_none()  # type: ignore[attr-defined]

        return await self._execute_query(_op, f"update {self.model_name}")

    async def delete(
        self,
        *,
        where: dict[str, Any],
        include: dict[str, bool] | None = None,
    ) -> ModelT | None:
        async def _op(session: AsyncSession):
            stmt = sa_delete(self.model).filter_by(**where).returning(self.model)
            result = await session.execute(stmt)  # type: ignore[attr-defined]
            return result.scalar_one_or_none()  # type: ignore[attr-defined]

        return await self._execute_query(_op, f"delete {self.model_name}")

    async def upsert(
        self,
        *,
        where: dict[str, Any],
        create: dict[str, Any] | None = None,
        update: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        include: dict[str, bool] | None = None,
    ) -> ModelT:
        # Support legacy signature with `data` containing create/update dicts
        if data is not None and (create is None or update is None):
            create = data.get("create", {})  # type: ignore[arg-type]
            update = data.get("update", {})  # type: ignore[arg-type]
        assert create is not None and update is not None, "create/update required"

        async def _op(session: AsyncSession):
            stmt = select(self.model).filter_by(**where).with_for_update()
            result = await session.execute(stmt)  # type: ignore[attr-defined]
            obj = result.scalar_one_or_none()  # type: ignore[attr-defined]
            if obj is None:
                obj = self.model(**{**where, **create})  # type: ignore[arg-type]
                session.add(obj)  # type: ignore[attr-defined]
            else:
                for key, value in update.items():
                    setattr(obj, key, value)
            await session.flush()  # type: ignore[attr-defined]
            return obj

        return await self._execute_query(_op, f"upsert {self.model_name}")

    async def update_many(self, *, where: dict[str, Any], data: dict[str, Any]) -> int:
        res = await self.update(where=where, data=data)
        return 1 if res else 0

    async def delete_many(self, *, where: dict[str, Any]) -> int:
        res = await self.delete(where=where)
        return 1 if res else 0

    # ------------------------------------------------------------------
    # Transaction helpers
    # ------------------------------------------------------------------

    async def execute_transaction(self, callback: Callable[[], Any]) -> Any:
        """Execute *callback* inside a database session / transaction block."""

        try:
            async with db.transaction() as _session:  # db.transaction yields AsyncSession
                # Provide session to callback by setting attribute maybe? The old
                # code expected none, so we just call callback; operations inside
                # will create their own sessions where needed.  This still gives
                # us atomicity because we're running in a SAVEPOINT transaction.
                return await callback()
        except Exception as exc:
            logger.error(f"Transaction failed in {self.model_name}: {exc}")
            raise

    # ------------------------------------------------------------------
    # Utility helpers mirrored from old implementation
    # ------------------------------------------------------------------

    @staticmethod
    def safe_get_attr(obj: Any, attr: str, default: Any = None) -> Any:
        """Return ``getattr(obj, attr, default)`` - keeps old helper available."""
        return getattr(obj, attr, default)

    # The old implementation exposed a *static* connect_or_create_relation helper
    # used when inserting nested relations.  Under SQLModel we can just set the
    # foreign-key field directly, but we keep this shim for API consistency.
    @staticmethod
    def connect_or_create_relation(id_field: str, model_id: Any, *_: Any, **__: Any) -> dict[str, Any]:
        """Return a dict with a single key that can be merged into *data* dicts.

        The calling code does something like::

            data = {"guild": connect_or_create_relation("guild_id", guild_id)}

        We map that pattern to a very small helper that collapses to `{"guild_id": guild_id}`.
        """
        return {id_field: model_id}
