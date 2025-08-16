from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Float, Index
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel
from tux.database.models.guild import Guild


class AFK(BaseModel, table=True):
    member_id: int = Field(primary_key=True, sa_type=BigInteger())
    nickname: str = Field(max_length=100)
    reason: str = Field(max_length=500)
    since: datetime = Field(default_factory=lambda: datetime.now(UTC))
    until: datetime | None = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())
    enforced: bool = Field(default=False)
    perm_afk: bool = Field(default=False)

    guild: "Guild" = Relationship()

    __table_args__ = (Index("idx_afk_member_guild", "member_id", "guild_id", unique=True),)


class Levels(BaseModel, table=True):
    member_id: int = Field(primary_key=True, sa_type=BigInteger())
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", sa_type=BigInteger())
    xp: float = Field(default=0.0, sa_type=Float())
    level: int = Field(default=0)
    blacklisted: bool = Field(default=False)
    last_message: datetime = Field(default_factory=lambda: datetime.now(UTC))

    guild: "Guild" = Relationship()

    __table_args__ = (Index("idx_levels_guild_xp", "guild_id", "xp"),)
