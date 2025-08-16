from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, TypeVar

from sqlalchemy import BigInteger, Boolean, DateTime, func, select, update as sa_update, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Automatic created_at and updated_at timestamps."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"onupdate": func.now()},
    )


class SoftDeleteMixin(SQLModel):
    """Soft delete functionality."""

    is_deleted: bool = Field(
        default=False,
        sa_type=Boolean(),
        sa_column_kwargs={"nullable": False, "server_default": "false"},
    )
    deleted_at: Optional[datetime] = Field(default=None, sa_type=DateTime(timezone=True))
    deleted_by: Optional[int] = Field(default=None, sa_type=BigInteger())

    def soft_delete(self, deleted_by_user_id: Optional[int] = None) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user_id


class AuditMixin(SQLModel):
    """Track who created/modified records."""
    created_by: Optional[int] = Field(default=None, sa_type=BigInteger())
    updated_by: Optional[int] = Field(default=None, sa_type=BigInteger())


class DiscordIDMixin(SQLModel):
    """Discord snowflake ID validation and utilities."""

    @staticmethod
    def validate_snowflake(snowflake_id: int, field_name: str = "id") -> int:
        if snowflake_id <= 0:
            raise ValueError(f"{field_name} must be a positive integer")
        if snowflake_id < 4194304:  # Minimum Discord snowflake
            raise ValueError(f"{field_name} is not a valid Discord snowflake")
        return snowflake_id


ModelT = TypeVar("ModelT", bound="BaseModel")


class CRUDMixin(SQLModel):
    """Minimal async CRUD helpers for SQLModel."""

    @classmethod
    async def create(cls, session: AsyncSession, /, **kwargs: Any) -> Any:
        instance = cls(**kwargs)
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    @classmethod
    async def get_by_id(cls, session: AsyncSession, record_id: Any) -> Any:
        return await session.get(cls, record_id)

    @classmethod
    async def find_one(cls, session: AsyncSession, filters: Any | None = None, order_by: Any | None = None):
        stmt = select(cls)
        if filters is not None:
            stmt = stmt.where(filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def find_all(
        cls,
        session: AsyncSession,
        filters: Any | None = None,
        order_by: Any | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ):
        stmt = select(cls)
        if filters is not None:
            stmt = stmt.where(filters)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        if limit is not None:
            stmt = stmt.limit(limit)
        if offset is not None:
            stmt = stmt.offset(offset)
        result = await session.execute(stmt)
        return result.scalars().all()

    @classmethod
    async def count(cls, session: AsyncSession, filters: Any | None = None) -> int:
        stmt = select(func.count()).select_from(cls)
        if filters is not None:
            stmt = stmt.where(filters)
        result = await session.execute(stmt)
        return int(result.scalar_one() or 0)

    @classmethod
    async def update_by_id(cls, session: AsyncSession, record_id: Any, /, **values: Any):
        instance = await session.get(cls, record_id)
        if instance is None:
            return None
        for key, value in values.items():
            setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    @classmethod
    async def update_where(cls, session: AsyncSession, filters: Any, values: dict[str, Any]) -> int:
        stmt = sa_update(cls).where(filters).values(**values)
        result = await session.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    @classmethod
    async def delete_by_id(cls, session: AsyncSession, record_id: Any) -> bool:
        instance = await session.get(cls, record_id)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True

    @classmethod
    async def delete_where(cls, session: AsyncSession, filters: Any) -> int:
        stmt = sa_delete(cls).where(filters)
        result = await session.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

    @classmethod
    async def upsert(
        cls,
        session: AsyncSession,
        match_filter: Any,
        create_values: dict[str, Any],
        update_values: dict[str, Any],
    ):
        existing = await cls.find_one(session, filters=match_filter)
        if existing is None:
            return await cls.create(session, **create_values)
        for key, value in update_values.items():
            setattr(existing, key, value)
        await session.flush()
        await session.refresh(existing)
        return existing


class BaseModel(TimestampMixin, SoftDeleteMixin, AuditMixin, CRUDMixin, DiscordIDMixin, SQLModel):
    """Full-featured base model for entities."""

    pass
