from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import BigInteger, Index
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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


class CustomCaseType(BaseModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})
    type_name: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    severity_level: int = Field(default=1)
    requires_duration: bool = Field(default=False)

    guild: Guild | None = Relationship()


class Case(BaseModel, table=True):
    case_id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    case_status: Optional[bool] = Field(default=True)

    case_type: Optional[CaseType] = Field(default=None)
    custom_case_type_id: Optional[int] = Field(default=None, foreign_key="customcasetype.id")

    case_reason: str = Field(max_length=2000)
    case_moderator_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    case_user_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    case_user_roles: List[int] = Field(default_factory=list)
    case_number: Optional[int] = Field(default=None)
    case_expires_at: Optional[datetime] = Field(default=None)
    case_metadata: Optional[dict] = Field(default=None)

    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})

    guild: Guild | None = Relationship()
    custom_case_type: Optional[CustomCaseType] = Relationship()

    __table_args__ = (
        Index("idx_case_guild_user", "guild_id", "case_user_id"),
        Index("idx_case_guild_moderator", "guild_id", "case_moderator_id"),
    )


class Note(BaseModel, table=True):
    note_id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    note_content: str = Field(max_length=2000)
    note_moderator_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    note_user_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    note_number: Optional[int] = Field(default=None)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})

    guild: Guild | None = Relationship()