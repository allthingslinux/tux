"""
Base Database Models for Tux Bot.

This module provides the foundational database models and utilities used
throughout the Tux bot's database layer, including base classes with
automatic timestamp management and serialization utilities.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast
from uuid import UUID, uuid4

import rich.repr
from pydantic import field_serializer
from sqlalchemy import DateTime, text
from sqlmodel import Field, SQLModel  # type: ignore[import]


class TimestampMixin:
    """Mixin providing automatic created_at and updated_at timestamp fields.

    This mixin adds database-managed timestamp fields that automatically
    set created_at on insert and update updated_at on every update.

    Usage:
        class MyModel(SQLModel, TimestampMixin, table=True):
            id: int | None = Field(default=None, primary_key=True)
            name: str
    """

    created_at: datetime | None = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
        nullable=True,
        description="Timestamp when the record was created",
    )

    updated_at: datetime | None = Field(
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP"),
        },
        nullable=True,
        description="Timestamp when the record was last updated",
    )


class BaseModel(SQLModel, TimestampMixin):
    """Base SQLModel class with automatic timestamp management.

    This class provides automatic created_at and updated_at timestamp fields
    that are managed by the database, along with serialization utilities for
    JSON responses.

    Attributes
    ----------
    created_at : datetime, optional
        Timestamp when the record was created (database-managed).
    updated_at : datetime, optional
        Timestamp when the record was last updated (database-managed).
    """

    # Allow SQLModel annotations without Mapped[] for SQLAlchemy 2.0 compatibility
    __allow_unmapped__ = True

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime | None) -> str | None:
        """Serialize datetime objects to ISO format strings.

        Parameters
        ----------
        value : datetime, optional
            The datetime value to serialize.

        Returns
        -------
        str, optional
            ISO format string representation of the datetime, or None if value is None.
        """
        return value.isoformat() if value else None

    def model_post_init(self, __context: Any) -> None:
        """Ensure timestamp fields are always present in __dict__ for compatibility.

        Even though timestamps are database-managed, some SQLAlchemy operations
        expect these fields to be accessible in the model's __dict__. This ensures
        compatibility without interfering with database defaults.
        """
        super().model_post_init(__context)
        # Ensure timestamp fields are always in __dict__ for SQLAlchemy compatibility
        # Only add them if they're not already present (don't override database values)
        if "created_at" not in self.__dict__:
            self.__dict__["created_at"] = None
        if "updated_at" not in self.__dict__:
            self.__dict__["updated_at"] = None

    def to_dict(
        self,
        include_relationships: bool = False,
        relationships: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Convert model instance to dictionary with relationship support.

        Parameters
        ----------
        include_relationships : bool, optional
            Whether to include relationship fields, by default False.
        relationships : list[str] | None, optional
            Specific relationships to include (if None, includes all), by default None.

        Returns
        -------
        dict[str, Any]
            Dictionary representation of the model.
        """
        data: dict[str, Any] = {}
        should_include_relationship = relationships is None

        for attr in self.__dict__:
            if attr.startswith("_"):  # Skip private attributes
                continue

            value = getattr(self, attr)

            # Handle special types first
            if isinstance(value, Enum):
                data[attr] = value.name
                continue
            if isinstance(value, datetime):
                data[attr] = value.isoformat()
                continue
            if isinstance(value, UUID):
                data[attr] = str(value)
                continue

            # Handle relationships if requested
            if not include_relationships:
                data[attr] = value
                continue

            # Check if this relationship should be included
            include_this_relationship = should_include_relationship or attr in (
                relationships or []
            )

            # Handle relationships based on type
            if isinstance(value, list):
                if (
                    include_this_relationship
                    and value
                    and all(
                        isinstance(item, BaseModel) for item in cast(list[Any], value)
                    )
                ):
                    model_items = cast(list[BaseModel], value)
                    data[attr] = [
                        model_item.to_dict(include_relationships, relationships)
                        for model_item in model_items
                    ]
                    continue
            elif isinstance(value, BaseModel):
                if include_this_relationship:
                    data[attr] = value.to_dict(include_relationships, relationships)
                    continue
                data[attr] = str(value)  # Just include ID for foreign keys
                continue

            data[attr] = value

        return data

    def __rich_repr__(self) -> rich.repr.Result:
        """Provide a Rich-formatted representation of the model.

        Yields
        ------
        tuple
            Positional or keyword arguments for the repr.
        """
        # We use __dict__ to get only the current instance's data
        # while avoiding full relationship traversal by default
        for attr, value in self.__dict__.items():
            if not attr.startswith("_"):
                yield attr, value


class UUIDMixin(SQLModel):
    """
    Mixin for models that need UUID primary keys.

    Provides:
    - id: UUID primary key with auto-generation
    - Proper indexing for performance
    """

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        description="Unique identifier (UUID) for the record",
    )


class SoftDeleteMixin(SQLModel):
    """
    Mixin for soft delete functionality.

    Provides:
    - deleted_at: Timestamp when record was soft-deleted
    - is_deleted: Boolean flag for soft delete status
    """

    deleted_at: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

    is_deleted: bool = Field(
        default=False,
        index=True,
        description="Flag indicating if record is soft-deleted",
    )

    @field_serializer("deleted_at")
    def serialize_deleted_at(self, value: datetime | None) -> str | None:
        """
        Serialize deleted_at field to ISO format string.

        Returns
        -------
        str | None
            ISO format datetime string, or None if value is None.
        """
        return value.isoformat() if value else None

    def soft_delete(self) -> None:
        """Mark record as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
