from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Index, JSON
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel
from tux.database.models.guild import Guild


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


class CustomCaseType(BaseModel, table=True):
    id: int = Field(primary_key=True, sa_type=BigInteger())
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())
    type_name: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    severity_level: int = Field(default=1)
    requires_duration: bool = Field(default=False)

    guild: Guild = Relationship()


class Case(BaseModel, table=True):
    case_id: int = Field(primary_key=True, sa_type=BigInteger())
    case_status: bool | None = Field(default=True)

    case_type: CaseType | None = Field(default=None)
    custom_case_type_id: int | None = Field(default=None, foreign_key="customcasetype.id")

    case_reason: str = Field(max_length=2000)
    case_moderator_id: int = Field(sa_type=BigInteger())
    case_user_id: int = Field(sa_type=BigInteger())
    case_user_roles: list[int] = Field(default_factory=list, sa_type=JSON())
    case_number: int | None = Field(default=None)
    case_expires_at: datetime | None = Field(default=None)
    case_metadata: dict[str, str] | None = Field(default=None, sa_type=JSON())

    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())

    guild: Guild = Relationship()
    custom_case_type: CustomCaseType = Relationship()

    __table_args__ = (
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
    )


class Note(BaseModel, table=True):
    note_id: int = Field(primary_key=True, sa_type=BigInteger())
    note_content: str = Field(max_length=2000)
    note_moderator_id: int = Field(sa_type=BigInteger())
    note_user_id: int = Field(sa_type=BigInteger())
    note_number: int | None = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())

    guild: Guild = Relationship()
