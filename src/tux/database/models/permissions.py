from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Index
from sqlmodel import Field

from tux.database.core.base import BaseModel


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
    id: int = Field(primary_key=True, sa_type=BigInteger)
    guild_id: int = Field(foreign_key="guild.guild_id", sa_type=BigInteger)

    permission_type: PermissionType
    access_type: AccessType

    target_id: int = Field(sa_type=BigInteger)
    target_name: str | None = Field(default=None, max_length=100)
    command_name: str | None = Field(default=None, max_length=100)
    module_name: str | None = Field(default=None, max_length=100)

    expires_at: datetime | None = Field(default=None)
    is_active: bool = Field(default=True)

    __table_args__ = (
        Index("idx_guild_perm_guild_type", "guild_id", "permission_type"),
        Index("idx_guild_perm_target", "target_id", "permission_type"),
    )
