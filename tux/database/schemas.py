from __future__ import annotations

from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

from sqlalchemy import BigInteger, Column, Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class GuildConfig(SQLModel, table=True):
    """Configuration settings associated with a guild"""

    guild_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    prefix: str | None = Field(default=None)
    mod_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    audit_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    join_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    private_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    report_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    dev_log_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    jail_channel_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    general_channel_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    starboard_channel_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_0_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_1_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_2_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_3_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_4_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_5_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_6_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    perm_level_7_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    base_staff_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    base_member_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    jail_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    quarantine_role_id: int | None = Field(default=None, sa_column=Column(BigInteger))

    guild: Guild = Relationship(back_populates="config")


class Levels(SQLModel, table=True):
    """Level information for a guild member"""

    member_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    xp: float = Field(default=0)
    level: int = Field(default=0, sa_column=Column(BigInteger))
    blacklisted: bool = Field(default=False)
    last_message: datetime = Field(default_factory=lambda: datetime.now(UTC))
    guild_id: int = Field(foreign_key="guild.guild_id", primary_key=True, sa_column=Column(BigInteger))

    guild: Guild = Relationship(back_populates="levels")


class Starboard(SQLModel, table=True):
    """Describes a starboard object for a guild"""

    guild_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    starboard_channel_id: int = Field(sa_column=Column(BigInteger))
    starboard_emoji: str = Field(nullable=False)
    starboard_threshold: int = Field(default=5, nullable=False)

    guild: Guild = Relationship(back_populates="starboards")


class StarboardMessage(SQLModel, table=True):
    """Describes a starboarded message"""

    message_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    message_content: str = Field(nullable=False)
    message_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_expires_at: datetime
    message_channel_id: int = Field(sa_column=Column(BigInteger))
    message_user_id: int = Field(sa_column=Column(BigInteger))
    message_guild_id: int = Field(index=True, sa_column=Column(BigInteger))
    star_count: int = Field(default=0)
    starboard_message_id: int = Field(nullable=False, sa_column=Column(BigInteger))

    guild: Guild = Relationship(back_populates="starboard_messages")

    __table_args__: Any = (UniqueConstraint("message_id", "message_guild_id"),)


class AFKModel(SQLModel, table=True):
    member_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    nickname: str
    reason: str
    since: datetime = Field(default_factory=datetime.now)
    until: datetime | None = Field(default=None)
    guild_id: int = Field(sa_column=Column(BigInteger), foreign_key="guild.guild_id")
    enforced: bool = Field(default=False)
    perm_afk: bool = Field(default=False)
    guild: Guild = Relationship(back_populates="afk_models")

    __table_args__ = (UniqueConstraint("member_id", "guild_id"),)


class Note(SQLModel, table=True):
    note_id: int = Field(primary_key=True, sa_column=Column(BigInteger), auto_increment=True)
    note_user_id: int = Field(sa_column=Column(BigInteger))
    note_moderator_id: int = Field(sa_column=Column(BigInteger))
    note_content: str
    note_created_at: datetime = Field(default_factory=datetime.now)
    note_number: int | None = Field(default=None)
    guild_id: int = Field(sa_column=Column(BigInteger), foreign_key="guild.guild_id")
    guild: Guild | None = Relationship(back_populates="notes")

    __table_args__ = (
        UniqueConstraint("note_number", "guild_id"),
        Index("index_note_number_guild_id", "note_number", "guild_id"),
    )


class CaseType(IntEnum):
    """Enumerator used to describe what action a case was logged for"""

    OTHER = -1
    BAN = 0
    UNBAN = 1
    HACKBAN = 2
    TEMPBAN = 3
    KICK = 4
    SNIPPETBAN = 5
    TIMEOUT = 6
    UNTIMEOUT = 7
    WARN = 8
    JAIL = 9
    UNJAIL = 10
    SNIPPETUNBAN = 11
    UNTEMPBAN = 12
    POLLBAN = 13
    POLLUNBAN = 14


class Case(SQLModel, table=True):
    """Entry describing a moderation case"""

    case_id: int = Field(primary_key=True, sa_column=Column(BigInteger), auto_increment=True)
    case_status: bool | None = Field(default=True)
    case_type: CaseType = Field(default=CaseType.OTHER)
    case_reason: str
    case_moderator_id: int = Field(sa_column=Column(BigInteger))
    case_user_id: int = Field(sa_column=Column(BigInteger))
    case_user_roles: list[int] = Field(default_factory=list)
    case_number: int | None = None
    case_created_at: datetime | None = Field(default_factory=datetime.now)
    case_expires_at: datetime | None = None
    case_tempban_expired: bool | None = Field(default=False)
    guild_id: int = Field(sa_column=Column(BigInteger), foreign_key="guild.guild_id")
    guild: Guild | None = Relationship(back_populates="cases")

    __table_args__ = (
        UniqueConstraint("case_number", "guild_id"),
        Index("index_case_number_guild_id", "case_number", "guild_id"),
        Index("index_guild_id_case_user_id", "guild_id", "case_user_id"),
        Index("index_guild_id_case_moderator_id", "guild_id", "case_moderator_id"),
        Index("index_guild_id_case_type", "guild_id", "case_type"),
        Index(
            "index_case_type_case_expires_at_tempban_expired", "case_type", "case_expires_at", "case_tempban_expired"
        ),
        Index("index_case_created_at_desc", "case_created_at", unique=False),
    )


class Reminder(SQLModel, table=True):
    """Stores a reminder set by a user"""

    reminder_id: int = Field(primary_key=True, sa_column=Column(BigInteger), auto_increment=True)
    reminder_content: str
    reminder_created_at: datetime = Field(default_factory=datetime.now)
    reminder_expires_at: datetime
    reminder_channel_id: int = Field(sa_column=Column(BigInteger))
    reminder_user_id: int = Field(sa_column=Column(BigInteger))
    reminder_sent: bool = Field(default=False)
    guild_id: int = Field(sa_column=Column(BigInteger), foreign_key="guild.guild_id")
    guild: Guild = Relationship(back_populates="reminders")


class Snippet(SQLModel, table=True):
    """Stores a snippet, asmall unit of information that users can quickly retrieve from the bot"""

    snippet_id: int = Field(primary_key=True, sa_column=Column(BigInteger), auto_increment=True)
    snippet_name: str
    snippet_content: str | None = None
    snippet_user_id: int = Field(sa_column=Column(BigInteger))
    snippet_created_at: datetime = Field(default_factory=datetime.now)
    guild_id: int = Field(sa_column=Column(BigInteger), foreign_key="guild.guild_id")
    uses: int = Field(default=0)
    locked: bool = Field(default=False)
    alias: str | None = None
    guild: Guild = Relationship(back_populates="snippets")

    __table_args__ = (
        UniqueConstraint("snippet_name", "guild_id"),
        Index("index_snippet_name_guild_id", "snippet_name", "guild_id"),
    )


class Guild(SQLModel, table=True):
    """Represents a guild and associated metadata"""

    guild_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    guild_joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    config: GuildConfig = Relationship(back_populates="guild")
    starboards: list[Starboard] | None = Relationship(back_populates="guild")
    levels: list[Levels] | None = Relationship(back_populates="guild")
    starboard_messages: list[StarboardMessage] | None = Relationship(back_populates="guild")
    afk_models: list[AFKModel] | None = Relationship(back_populates="guild")
    cases: list[Case] | None = Relationship(back_populates="guild")
    case_count: int = Field(default=0)
    snippets: list[Snippet] = Relationship(back_populates="guild")
    reminders: list[Reminder] = Relationship(back_populates="guild")
    notes: list[Note] = Relationship(back_populates="guild")
