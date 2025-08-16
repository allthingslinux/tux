from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, TypeVar

from sqlalchemy import BigInteger, Boolean, Column, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Automatic created_at and updated_at timestamps."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
    )


class SoftDeleteMixin(SQLModel):
    """Soft delete functionality."""

    is_deleted: bool = Field(default=False, sa_column=Column(Boolean, nullable=False, server_default="false"))
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    deleted_by: Optional[int] = Field(default=None, sa_column=Column(BigInteger))

    def soft_delete(self, deleted_by_user_id: Optional[int] = None) -> None:
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user_id


class AuditMixin(SQLModel):
    """Track who created/modified records."""

    created_by: Optional[int] = Field(default=None, sa_column=Column(BigInteger))
    updated_by: Optional[int] = Field(default=None, sa_column=Column(BigInteger))


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
    async def create(cls, session: AsyncSession, /, **kwargs: Any):
        instance = cls(**kwargs)  # type: ignore[call-arg]
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    @classmethod
    async def get_by_id(cls, session: AsyncSession, record_id: Any):
        return await session.get(cls, record_id)


class BaseModel(TimestampMixin, SoftDeleteMixin, AuditMixin, CRUDMixin, DiscordIDMixin, SQLModel):
    """Full-featured base model for entities."""

    pass