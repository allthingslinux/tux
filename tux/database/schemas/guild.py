from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import BigInteger, Column, Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class Guild(SQLModel, table=True):
    """Represents a guild and associated metadata"""

    guild_id: int = Field(primary_key=True, sa_column=Column(BigInteger))
    guild_joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    config: GuildConfig = Relationship(back_populates="guild")
    starboards: list[Starboard] | None = Relationship(back_populates="guild")
    levels: list[Levels] | None = Relationship(back_populates="guild")
    starboard_messages: list[StarboardMessage] | None = Relationship(back_populates="guild")
    case_count: int = Field(default=0)


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
    message_guild_id: int = Field(sa_column=Column(BigInteger))
    star_count: int = Field(default=0)
    starboard_message_id: int = Field(nullable=False, sa_column=Column(BigInteger))

    guild: Guild = Relationship(back_populates="starboard_messages")

    __table_args__: Any = (
        UniqueConstraint("message_id", "message_guild_id"),
        Index("idx_message_id_guild_id", "message_id", "message_guild_id"),
    )


""" old prisma schemas, remove when no longer needed.
model Guild {
  guild_id         BigInt             @id
  guild_joined_at  DateTime?          @default(now())
  cases            Case[]
  snippets         Snippet[]
  notes            Note[]
  reminders        Reminder[]
  guild_config     GuildConfig[]
  AFK              AFKModel[]
  Starboard        Starboard?
  StarboardMessage StarboardMessage[]
  case_count       BigInt             @default(0)
  levels           Levels[]

  @@index([guild_id])

}
"""
