from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Index
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel


class Guild(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, sa_type=BigInteger())
    guild_joined_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    case_count: int = Field(default=0)

    # Relationship provided via backref on GuildConfig

    __table_args__ = (Index("idx_guild_id", "guild_id"),)


class GuildConfig(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", sa_type=BigInteger())
    prefix: str | None = Field(default=None, max_length=10)

    mod_log_id: int | None = Field(default=None, sa_type=BigInteger())
    audit_log_id: int | None = Field(default=None, sa_type=BigInteger())
    join_log_id: int | None = Field(default=None, sa_type=BigInteger())
    private_log_id: int | None = Field(default=None, sa_type=BigInteger())
    report_log_id: int | None = Field(default=None, sa_type=BigInteger())
    dev_log_id: int | None = Field(default=None, sa_type=BigInteger())

    jail_channel_id: int | None = Field(default=None, sa_type=BigInteger())
    general_channel_id: int | None = Field(default=None, sa_type=BigInteger())
    starboard_channel_id: int | None = Field(default=None, sa_type=BigInteger())

    base_staff_role_id: int | None = Field(default=None, sa_type=BigInteger())
    base_member_role_id: int | None = Field(default=None, sa_type=BigInteger())
    jail_role_id: int | None = Field(default=None, sa_type=BigInteger())
    quarantine_role_id: int | None = Field(default=None, sa_type=BigInteger())

    perm_level_0_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_1_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_2_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_3_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_4_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_5_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_6_role_id: int | None = Field(default=None, sa_type=BigInteger())
    perm_level_7_role_id: int | None = Field(default=None, sa_type=BigInteger())

    guild: "Guild" = Relationship(sa_relationship_kwargs={"backref": "guild_config"})
