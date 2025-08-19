from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Column, Index, Integer, UniqueConstraint
from sqlalchemy import Enum as PgEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from tux.database.core.base import BaseModel


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
    id: int | None = Field(default=None, primary_key=True, sa_type=Integer())
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())
    type_name: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=500)
    severity_level: int = Field(default=1)
    requires_duration: bool = Field(default=False)


class Case(BaseModel, table=True):
    case_id: int | None = Field(default=None, primary_key=True, sa_type=Integer())
    case_status: bool | None = Field(default=True)

    case_type: CaseType | None = Field(
        default=None,
        sa_column=Column(PgEnum(CaseType, name="case_type_enum"), nullable=True),
    )
    custom_case_type_id: int | None = Field(default=None, foreign_key="custom_case_type.id")

    case_reason: str = Field(max_length=2000)
    case_moderator_id: int = Field(sa_type=BigInteger())
    case_user_id: int = Field(sa_type=BigInteger())
    case_user_roles: list[int] = Field(default_factory=list, sa_type=JSONB())
    case_number: int | None = Field(default=None)
    case_expires_at: datetime | None = Field(default=None)
    case_metadata: dict[str, str] | None = Field(default=None, sa_type=JSONB())

    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())

    __table_args__ = (
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
        UniqueConstraint("guild_id", "case_number", name="uq_case_guild_case_number"),
    )


class Note(BaseModel, table=True):
    note_id: int | None = Field(default=None, primary_key=True, sa_type=Integer())
    note_content: str = Field(max_length=2000)
    note_moderator_id: int = Field(sa_type=BigInteger())
    note_user_id: int = Field(sa_type=BigInteger())
    note_number: int | None = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger())
