from __future__ import annotations

from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional, Any, Callable, cast

from sqlmodel import Field as _SMField, Relationship, SQLModel
from sqlalchemy import Column, JSON

# Explicitly annotate Field callable to satisfy Pyright strict mode
Field = cast(Callable[..., Any], _SMField)


class CaseType(str, Enum):
    """Enumeration of moderation case types.

    This mirrors the values previously defined in the Prisma schema so that
    existing business-logic can continue to rely on the same string values.
    """

    BAN = "BAN"
    UNBAN = "UNBAN"
    HACKBAN = "HACKBAN"
    TEMPBAN = "TEMPBAN"
    KICK = "KICK"
    SNIPPETBAN = "SNIPPETBAN"
    TIMEOUT = "TIMEOUT"
    UNTIMEOUT = "UNTIMEOUT"
    WARN = "WARN"
    JAIL = "JAIL"
    UNJAIL = "UNJAIL"
    SNIPPETUNBAN = "SNIPPETUNBAN"
    UNTEMPBAN = "UNTEMPBAN"
    POLLBAN = "POLLBAN"
    POLLUNBAN = "POLLUNBAN"


class Guild(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, sa_column_kwargs={"index": True})
    guild_joined_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    case_count: int = Field(default=0, nullable=False)

    # --- relationships ---
    cases: list[Case] = Relationship(back_populates="guild")
    snippets: list[Snippet] = Relationship(back_populates="guild")
    notes: list[Note] = Relationship(back_populates="guild")
    reminders: list[Reminder] = Relationship(back_populates="guild")
    guild_config: GuildConfig | None = Relationship(back_populates="guild")
    afk_records: list[AFKModel] = Relationship(back_populates="guild")
    starboard: Starboard | None = Relationship(back_populates="guild")
    starboard_messages: list[StarboardMessage] = Relationship(back_populates="guild")
    levels: list[Levels] = Relationship(back_populates="guild")


class GuildConfig(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id")

    prefix: str | None = None
    mod_log_id: int | None = None
    audit_log_id: int | None = None
    join_log_id: int | None = None
    private_log_id: int | None = None
    report_log_id: int | None = None
    dev_log_id: int | None = None
    jail_channel_id: int | None = None
    general_channel_id: int | None = None
    starboard_channel_id: int | None = None

    perm_level_0_role_id: int | None = None
    perm_level_1_role_id: int | None = None
    perm_level_2_role_id: int | None = None
    perm_level_3_role_id: int | None = None
    perm_level_4_role_id: int | None = None
    perm_level_5_role_id: int | None = None
    perm_level_6_role_id: int | None = None
    perm_level_7_role_id: int | None = None

    base_staff_role_id: int | None = None
    base_member_role_id: int | None = None
    jail_role_id: int | None = None
    quarantine_role_id: int | None = None

    guild: Guild = Relationship(back_populates="guild_config")


class AFKModel(SQLModel, table=True):
    member_id: int = Field(primary_key=True)
    nickname: str
    reason: str
    since: datetime = Field(default_factory=lambda: datetime.now(UTC))
    until: datetime | None = None
    guild_id: int = Field(foreign_key="guild.guild_id")
    enforced: bool = Field(default=False)
    perm_afk: bool = Field(default=False)

    guild: Guild = Relationship(back_populates="afk_records")


class Levels(SQLModel, table=True):
    member_id: int = Field(primary_key=True)
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id")

    xp: float = Field(default=0)
    level: int = Field(default=0)
    blacklisted: bool = Field(default=False)
    last_message: datetime = Field(default_factory=lambda: datetime.now(UTC))

    guild: Guild = Relationship(back_populates="levels")

    __table_args__ = (
        # Composite unique constraint mirrors old @@unique([member_id, guild_id])
        {"sqlite_autoincrement": True},
    )


class Note(SQLModel, table=True):
    note_id: int | None = Field(default=None, primary_key=True)

    note_content: str
    note_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    note_moderator_id: int
    note_user_id: int
    note_number: int | None = Field(default=None)

    guild_id: int = Field(foreign_key="guild.guild_id")

    guild: Guild = Relationship(back_populates="notes")


class Case(SQLModel, table=True):
    case_id: int | None = Field(default=None, primary_key=True)

    case_status: bool | None = Field(default=True)
    case_type: CaseType
    case_reason: str
    case_moderator_id: int
    case_user_id: int
    case_user_roles: List[int] = Field(default_factory=list, sa_column=Column(JSON))
    case_number: int | None = None
    case_created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(UTC))
    case_expires_at: datetime | None = None
    case_tempban_expired: bool | None = Field(default=False)

    guild_id: int = Field(foreign_key="guild.guild_id")

    guild: Guild = Relationship(back_populates="cases")


class Reminder(SQLModel, table=True):
    reminder_id: int | None = Field(default=None, primary_key=True)

    reminder_content: str
    reminder_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    reminder_expires_at: datetime
    reminder_channel_id: int
    reminder_user_id: int
    reminder_sent: bool = Field(default=False)

    guild_id: int = Field(foreign_key="guild.guild_id")

    guild: Guild = Relationship(back_populates="reminders")


class Snippet(SQLModel, table=True):
    snippet_id: int | None = Field(default=None, primary_key=True)

    snippet_name: str
    snippet_content: str | None = None
    snippet_user_id: int
    snippet_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    guild_id: int = Field(foreign_key="guild.guild_id")
    uses: int = Field(default=0)
    locked: bool = Field(default=False)
    alias: str | None = None

    guild: Guild = Relationship(back_populates="snippets")


class Starboard(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id")

    starboard_channel_id: int
    starboard_emoji: str
    starboard_threshold: int

    guild: Guild = Relationship(back_populates="starboard")


class StarboardMessage(SQLModel, table=True):
    message_id: int = Field(primary_key=True)

    message_content: str
    message_created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_expires_at: datetime
    message_channel_id: int
    message_user_id: int
    message_guild_id: int = Field(foreign_key="guild.guild_id")
    star_count: int = Field(default=0)
    starboard_message_id: int

    guild: Guild = Relationship(back_populates="starboard_messages")
