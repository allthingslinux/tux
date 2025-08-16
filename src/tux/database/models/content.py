from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Index
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel
from tux.database.models.guild import Guild


class Snippet(BaseModel, table=True):
    snippet_id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    snippet_name: str = Field(max_length=100)
    snippet_content: Optional[str] = Field(default=None, max_length=4000)
    snippet_user_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})
    uses: int = Field(default=0)
    locked: bool = Field(default=False)
    alias: Optional[str] = Field(default=None, max_length=100)

    guild: Guild | None = Relationship()

    __table_args__ = (Index("idx_snippet_name_guild", "snippet_name", "guild_id", unique=True),)


class Reminder(BaseModel, table=True):
    reminder_id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    reminder_content: str = Field(max_length=2000)
    reminder_expires_at: datetime
    reminder_channel_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    reminder_user_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    reminder_sent: bool = Field(default=False)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})

    guild: Guild | None = Relationship()