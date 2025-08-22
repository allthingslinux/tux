from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from tux.database.controllers.base import BaseController
from tux.database.models.guild import Guild, GuildConfig
from tux.database.service import DatabaseService


class GuildController(BaseController[Guild]):
    """Clean Guild controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(Guild, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_guild_by_id(self, guild_id: int) -> Guild | None:
        """Get a guild by its ID."""
        return await self.get_by_id(guild_id)

    async def get_or_create_guild(self, guild_id: int) -> Guild:
        """Get a guild by ID, or create it if it doesn't exist."""
        guild, _ = await self.get_or_create(guild_id=guild_id)
        return guild

    async def create_guild(self, guild_id: int) -> Guild:
        """Create a new guild."""
        return await self.create(guild_id=guild_id)

    async def delete_guild(self, guild_id: int) -> bool:
        """Delete a guild by ID."""
        return await self.delete_by_id(guild_id)

    # GuildConfig methods using with_session for cross-model operations
    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        """Get guild configuration."""

        async def _op(session: AsyncSession) -> GuildConfig | None:
            return await session.get(GuildConfig, guild_id)

        return await self.with_session(_op)

    async def update_guild_config(self, guild_id: int, data: dict[str, Any]) -> GuildConfig:
        """Update guild configuration."""

        async def _op(session: AsyncSession) -> GuildConfig:
            config = await session.get(GuildConfig, guild_id)
            if config is None:
                config = GuildConfig(guild_id=guild_id, **data)
                session.add(config)
            else:
                for key, value in data.items():
                    setattr(config, key, value)
            await session.flush()
            await session.refresh(config)
            return config

        return await self.with_session(_op)

    async def get_all_guilds(self) -> list[Guild]:
        """Get all guilds."""
        return await self.find_all()

    async def get_guild_count(self) -> int:
        """Get the total number of guilds."""
        return await self.count()

    # Additional methods that module files expect
    async def find_many(self, **filters: Any) -> list[Guild]:
        """Find many guilds with optional filters - alias for find_all."""
        return await self.find_all()

    async def insert_guild_by_id(self, guild_id: int, **kwargs: Any) -> Guild:
        """Insert a new guild by ID."""
        return await self.create(guild_id=guild_id, **kwargs)

    async def delete_guild_by_id(self, guild_id: int) -> bool:
        """Delete a guild by ID."""
        return await self.delete_by_id(guild_id)
