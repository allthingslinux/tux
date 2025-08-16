from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger, Index
from sqlmodel import Field, Relationship

from tux.database.core.base import BaseModel


class Guild(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, sa_column_kwargs={"type_": BigInteger()})
    guild_joined_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    case_count: int = Field(default=0)

    guild_config: GuildConfig | None = Relationship(back_populates="guild")

    __table_args__ = (Index("idx_guild_id", "guild_id"),)


class GuildConfig(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, foreign_key="guild.guild_id", sa_column_kwargs={"type_": BigInteger()})
    prefix: str | None = Field(default=None, max_length=10)

    mod_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    audit_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    join_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    private_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    report_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    dev_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})

    jail_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    general_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    starboard_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})

    base_staff_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    base_member_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    jail_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    quarantine_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})

    perm_level_0_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_1_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_2_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_3_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_4_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_5_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_6_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})
    perm_level_7_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger()})

    guild: Guild = Relationship(back_populates="guild_config")
