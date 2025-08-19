from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Index
from sqlmodel import Field

from tux.database.core.base import BaseModel


class Starboard(BaseModel, table=True):
    guild_id: int = Field(primary_key=True, sa_type=BigInteger)
    starboard_channel_id: int = Field(sa_type=BigInteger)
    starboard_emoji: str = Field(max_length=64)
    starboard_threshold: int = Field(default=1)


class StarboardMessage(BaseModel, table=True):
    message_id: int = Field(primary_key=True, sa_type=BigInteger)
    message_content: str = Field(max_length=4000)
    message_expires_at: datetime = Field()
    message_channel_id: int = Field(sa_type=BigInteger)
    message_user_id: int = Field(sa_type=BigInteger)
    message_guild_id: int = Field(sa_type=BigInteger)
    star_count: int = Field(default=0)
    starboard_message_id: int = Field(sa_type=BigInteger)

    __table_args__ = (Index("ux_starboard_message", "message_id", "message_guild_id", unique=True),)
