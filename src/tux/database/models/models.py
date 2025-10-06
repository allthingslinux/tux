from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import ARRAY, JSON, BigInteger, CheckConstraint, Column, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy import Enum as PgEnum
from sqlalchemy.orm import Mapped, relationship
from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel
from .enums import CaseType, OnboardingStage


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
    permission_ranks = Relationship(
        sa_relationship=relationship(
            "GuildPermissionRank",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
        ),
    )
    command_permissions = Relationship(
        sa_relationship=relationship(
            "GuildCommandPermission",
            back_populates="guild",
            cascade="all, delete",
            passive_deletes=True,
            lazy="selectin",
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

    guild: Mapped[Guild] = Relationship(sa_relationship=relationship(back_populates="reminders"))

    __table_args__ = (
        Index("idx_reminder_expires_at", "reminder_expires_at"),
        Index("idx_reminder_user", "reminder_user_id"),
        Index("idx_reminder_sent", "reminder_sent"),
        Index("idx_reminder_guild_expires", "guild_id", "reminder_expires_at"),
    )


class GuildConfig(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", ondelete="CASCADE", sa_type=BigInteger)
    prefix: str = Field(default="$", max_length=3)

    mod_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log mod cases
    audit_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log guild events
    join_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log joins and leaves
    private_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log edits, deletes, etc
    report_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log reports and other important events
    dev_log_id: int | None = Field(default=None, sa_type=BigInteger)  # log dev events / tux verbose logs / sentry

    jail_channel_id: int | None = Field(default=None, sa_type=BigInteger)

    jail_role_id: int | None = Field(default=None, sa_type=BigInteger)

    # Onboarding tracking
    onboarding_completed: bool = Field(default=False)
    onboarding_stage: OnboardingStage | None = Field(
        default=None,
        sa_column=Column(PgEnum(OnboardingStage, name="onboarding_stage_enum"), nullable=True),
    )

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

    # Discord message ID for audit log message - allows editing the message if case is updated
    audit_log_message_id: int | None = Field(default=None, sa_type=BigInteger)

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


class Note(BaseModel, table=True):
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


# ===== DYNAMIC PERMISSION SYSTEM =====


class GuildPermissionRank(BaseModel, table=True):
    """Dynamic permission ranks that servers can customize."""

    __tablename__ = "guild_permission_ranks"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    guild_id: int = Field(
        foreign_key="guild.guild_id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        index=True,
    )
    rank: int = Field(sa_type=Integer)  # 0-100 (permission rank hierarchy)
    name: str = Field(max_length=100)  # "Junior Mod", "Moderator", etc.
    description: str | None = Field(default=None, max_length=500)
    color: int | None = Field(default=None, sa_type=Integer)  # Role color for UI # TODO: remove
    position: int = Field(default=0, sa_type=Integer)  # Display order # TODO: remove
    enabled: bool = Field(default=True)  # TODO: remove

    # Relationship to Guild
    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            back_populates="permission_ranks",
            lazy="selectin",
        ),
    )

    # Relationship to permission assignments
    assignments = Relationship(
        sa_relationship=relationship(
            "GuildPermissionAssignment",
            back_populates="permission_rank",
            cascade="all, delete-orphan",
            passive_deletes=True,
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint("rank >= 0 AND rank <= 100", name="check_rank_range"),
        CheckConstraint("position >= 0", name="check_position_positive"),
        UniqueConstraint("guild_id", "rank", name="unique_guild_permission_rank"),
        UniqueConstraint("guild_id", "name", name="unique_guild_permission_rank_name"),
        Index("idx_guild_perm_ranks_guild", "guild_id"),
        Index("idx_guild_perm_ranks_position", "guild_id", "position"),
    )


class GuildPermissionAssignment(BaseModel, table=True):
    """Assigns permission ranks to Discord roles in each server."""

    __tablename__ = "guild_permission_assignments"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    guild_id: int = Field(
        foreign_key="guild.guild_id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        index=True,
    )
    permission_rank_id: int = Field(
        foreign_key="guild_permission_ranks.id",
        ondelete="CASCADE",
        sa_type=Integer,
        index=True,
    )
    role_id: int = Field(sa_type=BigInteger, index=True)
    assigned_by: int = Field(sa_type=BigInteger)  # User who assigned it
    assigned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    permission_rank = Relationship(
        sa_relationship=relationship(
            "GuildPermissionRank",
            back_populates="assignments",
            lazy="selectin",
        ),
    )

    __table_args__ = (
        UniqueConstraint("guild_id", "role_id", name="unique_guild_role_assignment"),
        Index("idx_guild_perm_assignments_guild", "guild_id"),
        Index("idx_guild_perm_assignments_rank", "permission_rank_id"),
        Index("idx_guild_perm_assignments_role", "role_id"),
    )


class GuildCommandPermission(BaseModel, table=True):
    """Assigns permission requirements to specific commands."""

    __tablename__ = "guild_command_permissions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    guild_id: int = Field(
        foreign_key="guild.guild_id",
        ondelete="CASCADE",
        sa_type=BigInteger,
        index=True,
    )
    command_name: str = Field(max_length=200, index=True)  # "ban", "kick", etc.
    required_rank: int = Field(sa_type=Integer)  # Permission rank required (0-100)
    category: str | None = Field(default=None, max_length=100)  # "moderation", "admin", etc.
    description: str | None = Field(default=None, max_length=500)
    enabled: bool = Field(default=True)

    # Relationship to Guild
    guild: Mapped[Guild] = Relationship(
        sa_relationship=relationship(
            "Guild",
            back_populates="command_permissions",
            lazy="selectin",
        ),
    )

    __table_args__ = (
        CheckConstraint("required_rank >= 0 AND required_rank <= 100", name="check_required_rank_range"),
        UniqueConstraint("guild_id", "command_name", name="unique_guild_command"),
        Index("idx_guild_cmd_perms_guild", "guild_id"),
        Index("idx_guild_cmd_perms_category", "guild_id", "category"),
        Index("idx_guild_cmd_perms_rank", "required_rank"),
    )
