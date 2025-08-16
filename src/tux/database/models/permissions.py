from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Index
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel
from tux.database.models.guild import Guild


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


class GuildPermission(BaseModel, table=True):
    id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    guild_id: int = Field(foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})

    permission_type: PermissionType
    access_type: AccessType

    target_id: int = Field(sa_column_kwargs={"type_": BigInteger()})
    target_name: str | None = Field(default=None, max_length=100)
    command_name: str | None = Field(default=None, max_length=100)
    module_name: str | None = Field(default=None, max_length=100)

    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)

    guild: Guild | None = Relationship()

    __table_args__ = (
        Index("idx_guild_perm_guild_type", "guild_id", "permission_type"),
        Index("idx_guild_perm_target", "target_id", "permission_type"),
    )
