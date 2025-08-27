from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, cast
from uuid import UUID, uuid4

from pydantic import field_serializer
from sqlalchemy import ARRAY, JSON, BigInteger, Column, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy import Enum as PgEnum
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

# =============================================================================
# Base Model Mixins - Professional Patterns from SQLModel Examples
# =============================================================================


class BaseModel(SQLModel):
    """
    Base model with serialization capabilities.

    Provides to_dict() method for converting model instances to dictionaries,
    with support for relationship inclusion and enum handling.
    """

    def to_dict(self, include_relationships: bool = False, relationships: list[str] | None = None) -> dict[str, Any]:
        """
        Convert model instance to dictionary with relationship support.

        Args:
            include_relationships: Whether to include relationship fields
            relationships: Specific relationships to include (if None, includes all)

        Returns:
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


class TimestampMixin(SQLModel):
    """
    Mixin for automatic timestamp management.

    Provides:
    - created_at: Set once when record is created
    - updated_at: Updated on every modification (database-level)
    """

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        description="Timestamp for record creation",
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"},
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        description="Timestamp for last record update",
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP", "onupdate": "CURRENT_TIMESTAMP"},
    )

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format strings."""
        return value.isoformat() if value else None


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


class PermissionType(str, Enum):
    MEMBER = "member"
    CHANNEL = "channel"
    CATEGORY = "category"
    ROLE = "role"
    COMMAND = "command"
    MODULE = "module"


class AccessType(str, Enum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"
    IGNORE = "ignore"


class CaseType(str, Enum):
    BAN = "BAN"
    UNBAN = "UNBAN"
    HACKBAN = "HACKBAN"
    TEMPBAN = "TEMPBAN"
    KICK = "KICK"
    TIMEOUT = "TIMEOUT"
    UNTIMEOUT = "UNTIMEOUT"
    WARN = "WARN"
    JAIL = "JAIL"
    UNJAIL = "UNJAIL"
    SNIPPETBAN = "SNIPPETBAN"
    SNIPPETUNBAN = "SNIPPETUNBAN"
    POLLBAN = "POLLBAN"
    POLLUNBAN = "POLLUNBAN"


class Guild(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, sa_type=BigInteger)
    guild_joined_at: datetime | None = Field(default_factory=datetime.now)
    case_count: int = Field(default=0)

    # PostgreSQL-specific features based on py-pglite examples
    guild_metadata: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Flexible metadata storage using PostgreSQL JSONB",
    )
    tags: list[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String)),
        description="Guild tags using PostgreSQL arrays",
    )
    feature_flags: dict[str, bool] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Feature toggles stored as JSON",
    )

    # Relationships with cascade delete - using sa_relationship to bypass SQLModel parsing issues
    snippets = Relationship(
        sa_relationship=relationship(
            "Snippet",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    cases = Relationship(
        sa_relationship=relationship(
            "Case",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    notes = Relationship(
        sa_relationship=relationship(
            "Note",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    reminders = Relationship(
        sa_relationship=relationship(
            "Reminder",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    afks = Relationship(
        sa_relationship=relationship(
            "AFK",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    levels_entries = Relationship(
        sa_relationship=relationship(
            "Levels",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    starboard_messages = Relationship(
        sa_relationship=relationship(
            "StarboardMessage",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    permissions = Relationship(
        sa_relationship=relationship(
            "GuildPermission",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )

    # One-to-one relationships
    guild_config = Relationship(
        sa_relationship=relationship(
            "GuildConfig",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="joined",
        ),
    )
    starboard = Relationship(
        sa_relationship=relationship(
            "Starboard",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="joined",
        ),
    )

    __table_args__ = (Index("idx_guild_id", "guild_id"),)


class Snippet(SQLModel, table=True):
    snippet_id: int | None = Field(default=None, primary_key=True, sa_type=Integer)
    snippet_name: str = Field(max_length=100)
    snippet_content: str | None = Field(default=None, max_length=4000)
    snippet_user_id: int = Field(sa_type=BigInteger)
    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    uses: int = Field(default=0)
    locked: bool = Field(default=False)
    alias: str | None = Field(default=None, max_length=100)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="snippets"))

    __table_args__ = (
        Index("idx_snippet_name_guild", "snippet_name", "guild_id", unique=True),
        Index("idx_snippet_user", "snippet_user_id"),
        Index("idx_snippet_uses", "uses"),
    )


class Reminder(SQLModel, table=True):
    reminder_id: int | None = Field(default=None, primary_key=True, sa_type=Integer)
    reminder_content: str = Field(max_length=2000)
    reminder_expires_at: datetime
    reminder_channel_id: int = Field(sa_type=BigInteger)
    reminder_user_id: int = Field(sa_type=BigInteger)
    reminder_sent: bool = Field(default=False)
    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="reminders"))

    __table_args__ = (
        Index("idx_reminder_expires_at", "reminder_expires_at"),
        Index("idx_reminder_user", "reminder_user_id"),
        Index("idx_reminder_sent", "reminder_sent"),
        Index("idx_reminder_guild_expires", "guild_id", "reminder_expires_at"),
    )


class GuildConfig(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    prefix: str | None = Field(default=None, max_length=10)

    mod_log_id: int | None = Field(default=None, sa_type=BigInteger)
    audit_log_id: int | None = Field(default=None, sa_type=BigInteger)
    join_log_id: int | None = Field(default=None, sa_type=BigInteger)
    private_log_id: int | None = Field(default=None, sa_type=BigInteger)
    report_log_id: int | None = Field(default=None, sa_type=BigInteger)
    dev_log_id: int | None = Field(default=None, sa_type=BigInteger)

    jail_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    general_channel_id: int | None = Field(default=None, sa_type=BigInteger)
    starboard_channel_id: int | None = Field(default=None, sa_type=BigInteger)

    base_staff_role_id: int | None = Field(default=None, sa_type=BigInteger)
    base_member_role_id: int | None = Field(default=None, sa_type=BigInteger)
    jail_role_id: int | None = Field(default=None, sa_type=BigInteger)
    quarantine_role_id: int | None = Field(default=None, sa_type=BigInteger)

    perm_level_0_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_1_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_2_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_3_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_4_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_5_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_6_role_id: int | None = Field(default=None, sa_type=BigInteger)
    perm_level_7_role_id: int | None = Field(default=None, sa_type=BigInteger)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="guild_config"))


class Case(BaseModel, table=True):
    # case is a reserved word in postgres, so we need to use a custom table name
    __tablename__ = "cases"  # pyright: ignore[reportAssignmentType]

    case_id: int | None = Field(default=None, primary_key=True, sa_type=Integer)
    case_status: bool = Field(default=True)

    case_type: CaseType | None = Field(
        default=None,
        sa_column=Column(PgEnum(CaseType, name="case_type_enum"), nullable=True),
    )

    case_reason: str = Field(max_length=2000)
    case_moderator_id: int = Field(sa_type=BigInteger)
    case_user_id: int = Field(sa_type=BigInteger)
    case_user_roles: list[int] = Field(default_factory=list, sa_type=JSON)
    case_number: int | None = Field(default=None)
    case_expires_at: datetime | None = Field(default=None)
    case_metadata: dict[str, str] | None = Field(default=None, sa_type=JSON)

    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="cases"))

    __table_args__ = (
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
        Index("idx_case_type", "case_type"),
        Index("idx_case_status", "case_status"),
        Index("idx_case_expires_at", "case_expires_at"),
        Index("idx_case_number", "case_number"),
        UniqueConstraint("guild_id", "case_number", name="uq_case_guild_case_number"),
    )


class Note(SQLModel, table=True):
    note_id: int | None = Field(default=None, primary_key=True, sa_type=Integer)
    note_content: str = Field(max_length=2000)
    note_moderator_id: int = Field(sa_type=BigInteger)
    note_user_id: int = Field(sa_type=BigInteger)
    note_number: int | None = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="notes"))

    __table_args__ = (
        Index("idx_note_user", "note_user_id"),
        Index("idx_note_moderator", "note_moderator_id"),
        Index("idx_note_guild_number", "guild_id", "note_number"),
        UniqueConstraint("guild_id", "note_number", name="uq_note_guild_note_number"),
    )


class GuildPermission(SQLModel, table=True):
    id: int = Field(primary_key=True, sa_type=BigInteger)
    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)

    permission_type: PermissionType
    access_type: AccessType

    target_id: int = Field(sa_type=BigInteger)
    target_name: str | None = Field(default=None, max_length=100)
    command_name: str | None = Field(default=None, max_length=100)
    module_name: str | None = Field(default=None, max_length=100)

    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="permissions"))

    __table_args__ = (
        Index("idx_guild_perm_guild_type", "guild_id", "permission_type"),
        Index("idx_guild_perm_target", "target_id", "permission_type"),
        Index("idx_guild_perm_active", "is_active"),
        Index("idx_guild_perm_expires", "expires_at"),
        Index("idx_guild_perm_guild_active", "guild_id", "is_active"),
    )


class AFK(SQLModel, table=True):
    member_id: int = Field(primary_key=True, sa_type=BigInteger)
    nickname: str = Field(max_length=100)
    reason: str = Field(max_length=500)
    since: datetime = Field(default_factory=lambda: datetime.now(UTC))
    until: datetime | None = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    enforced: bool = Field(default=False)
    perm_afk: bool = Field(default=False)

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="afks"))

    __table_args__ = (
        Index("idx_afk_member_guild", "member_id", "guild_id", unique=True),
        Index("idx_afk_guild", "guild_id"),
        Index("idx_afk_enforced", "enforced"),
        Index("idx_afk_perm", "perm_afk"),
        Index("idx_afk_until", "until"),
    )


class Levels(SQLModel, table=True):
    member_id: int = Field(primary_key=True, sa_type=BigInteger)
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    xp: float = Field(default=0.0, sa_type=Float)
    level: int = Field(default=0)
    blacklisted: bool = Field(default=False)
    last_message: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationship back to Guild - using sa_relationship
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="levels_entries"))

    __table_args__ = (
        Index("idx_levels_guild_xp", "guild_id", "xp"),
        Index("idx_levels_member", "member_id"),
        Index("idx_levels_level", "level"),
        Index("idx_levels_blacklisted", "blacklisted"),
        Index("idx_levels_last_message", "last_message"),
    )


class Starboard(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    starboard_channel_id: int = Field(sa_type=BigInteger)
    starboard_emoji: str = Field(max_length=64)
    starboard_threshold: int = Field(default=1)

    # Relationship back to Guild - using proper SQLAlchemy 2.0 style
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="starboard"))

    __table_args__ = (
        Index("idx_starboard_channel", "starboard_channel_id"),
        Index("idx_starboard_threshold", "starboard_threshold"),
    )


class StarboardMessage(SQLModel, table=True):
    message_id: int = Field(primary_key=True, sa_type=BigInteger)
    message_content: str = Field(max_length=4000)
    message_expires_at: datetime = Field()
    message_channel_id: int = Field(sa_type=BigInteger)
    message_user_id: int = Field(sa_type=BigInteger)
    message_guild_id: int = Field(foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    star_count: int = Field(default=0)
    starboard_message_id: int = Field(sa_type=BigInteger)

    # Relationship back to Guild - using proper SQLAlchemy 2.0 style
    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="starboard_messages"))

    __table_args__ = (
        Index("ux_starboard_message", "message_id", "message_guild_id", unique=True),
        Index("idx_starboard_msg_expires", "message_expires_at"),
        Index("idx_starboard_msg_user", "message_user_id"),
        Index("idx_starboard_msg_channel", "message_channel_id"),
        Index("idx_starboard_msg_star_count", "star_count"),
    )
