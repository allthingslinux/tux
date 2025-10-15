from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import field_serializer
from sqlalchemy import text
from sqlmodel import Field, SQLModel


class BaseModel(SQLModel):
    """
    Base model with serialization capabilities and automatic timestamp management.

    Provides to_dict() method for converting model instances to dictionaries,
    with support for relationship inclusion and enum handling.

    Automatically includes created_at and updated_at timestamps for all models.
    """

    # Allow SQLModel annotations without Mapped[] for SQLAlchemy 2.0 compatibility
    __allow_unmapped__ = True

    # Timestamp fields
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        description="Timestamp for record creation",
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")},
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        description="Timestamp for last record update",
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP"), "onupdate": text("CURRENT_TIMESTAMP")},
    )

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format strings."""
        return value.isoformat() if value else None

    def to_dict(self, include_relationships: bool = False, relationships: list[str] | None = None) -> dict[str, Any]:
        """
        Convert model instance to dictionary with relationship support.

        Args:
            include_relationships: Whether to include relationship fields
            relationships: Specific relationships to include (if None, includes all)

        Returns
        -------
            Dictionary representation of the model
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
            include_this_relationship = should_include_relationship or attr in (relationships or [])

            # Handle relationships based on type
            if isinstance(value, list):
                if (
                    include_this_relationship
                    and value
                    and all(isinstance(item, BaseModel) for item in cast(list[Any], value))
                ):
                    model_items = cast(list[BaseModel], value)
                    data[attr] = [
                        model_item.to_dict(include_relationships, relationships) for model_item in model_items
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

    deleted_at: datetime | None = Field(
        default=None,
        description="Timestamp for soft deletion",
    )

    is_deleted: bool = Field(
        default=False,
        index=True,
        description="Flag indicating if record is soft-deleted",
    )

    @field_serializer("deleted_at")
    def serialize_deleted_at(self, value: datetime | None) -> str | None:
        """Serialize deleted_at field to ISO format string."""
        return value.isoformat() if value else None

    def soft_delete(self) -> None:
        """Mark record as soft-deleted."""
        self.is_deleted = True
        self.deleted_at = datetime.now(UTC)

    def restore(self) -> None:
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
