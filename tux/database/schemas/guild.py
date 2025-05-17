from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import BigInteger
from sqlmodel import Field, Relationship, SQLModel


# TODO: fill this in with relations to other schemas after they are written
class Guild(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, index=True, sa_column_kwargs={"type_": BigInteger})
    guild_joined_at: datetime | None = Field(default_factory=lambda: datetime.now(UTC))
    config: GuildConfig = Relationship(back_populates="guild")
    case_count: int = Field(default=0)


class GuildConfig(SQLModel, table=True):
    guild_id: int = Field(primary_key=True, unique=True, sa_column_kwargs={"type_": BigInteger})
    prefix: str | None = Field(default=None)
    mod_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    audit_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    join_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    private_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    report_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    dev_log_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    jail_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    general_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    starboard_channel_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_0_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_1_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_2_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_3_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_4_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_5_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_6_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    perm_level_7_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    base_staff_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    base_member_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    jail_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})
    quarantine_role_id: int | None = Field(default=None, sa_column_kwargs={"type_": BigInteger})

    guild: Guild = Relationship(back_populates="config")


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

model GuildConfig {
  prefix               String?
  mod_log_id           BigInt?
  audit_log_id         BigInt?
  join_log_id          BigInt?
  private_log_id       BigInt?
  report_log_id        BigInt?
  dev_log_id           BigInt?
  jail_channel_id      BigInt?
  general_channel_id   BigInt?
  starboard_channel_id BigInt?
  perm_level_0_role_id BigInt?
  perm_level_1_role_id BigInt?
  perm_level_2_role_id BigInt?
  perm_level_3_role_id BigInt?
  perm_level_4_role_id BigInt?
  perm_level_5_role_id BigInt?
  perm_level_6_role_id BigInt?
  perm_level_7_role_id BigInt?
  base_staff_role_id   BigInt?
  base_member_role_id  BigInt?
  jail_role_id         BigInt?
  quarantine_role_id   BigInt?
  guild_id             BigInt  @id @unique
  guild                Guild   @relation(fields: [guild_id], references: [guild_id])

  @@index([guild_id])
}

}
"""
