"""
Guild and guild configuration management controller.

This controller manages Discord guild records and their associated configuration
settings, providing methods for guild lifecycle management and configuration updates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import Guild, GuildConfig

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from tux.database.service import DatabaseService


class GuildController(BaseController[Guild]):
    """Clean Guild controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the guild controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Guild, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_guild_by_id(self, guild_id: int) -> Guild | None:
        """
        Get a guild by its ID.

        Returns
        -------
        Guild | None
            The guild if found, None otherwise.
        """
        return await self.get_by_id(guild_id)

    async def get_or_create_guild(self, guild_id: int) -> Guild:
        """
        Get a guild by ID, or create it if it doesn't exist.

        Returns
        -------
        Guild
            The guild (existing or newly created).
        """
        guild, _ = await self.get_or_create(id=guild_id)
        return guild

    async def create_guild(self, guild_id: int) -> Guild:
        """
        Create a new guild.

        Returns
        -------
        Guild
            The newly created guild.
        """
        return await self.create(id=guild_id)

    async def delete_guild(self, guild_id: int) -> bool:
        """
        Delete a guild by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(guild_id)

    # GuildConfig methods using with_session for cross-model operations
    async def get_guild_config(self, guild_id: int) -> GuildConfig | None:
        """
        Get guild configuration.

        Returns
        -------
        GuildConfig | None
            The guild configuration if found, None otherwise.
        """

        async def _op(session: AsyncSession) -> GuildConfig | None:
            """Get guild config by guild ID.

            Parameters
            ----------
            session : AsyncSession
                The database session to use.

            Returns
            -------
            GuildConfig | None
                The guild configuration or None if not found.
            """
            return await session.get(GuildConfig, guild_id)

        return await self.with_session(_op)

    async def update_guild_config(
        self,
        guild_id: int,
        data: dict[str, Any],
    ) -> GuildConfig:
        """
        Update guild configuration.

        Returns
        -------
        GuildConfig
            The updated guild configuration.
        """

        async def _op(session: AsyncSession) -> GuildConfig:
            """Update or create guild configuration.

            Parameters
            ----------
            session : AsyncSession
                The database session to use.

            Returns
            -------
            GuildConfig
                The updated or created guild configuration.
            """
            config = await session.get(GuildConfig, guild_id)
            if config is None:
                config = GuildConfig(id=guild_id, **data)
                session.add(config)
            else:
                for key, value in data.items():
                    setattr(config, key, value)
            await session.flush()
            await session.refresh(config)
            return config

        return await self.with_session(_op)

    async def get_all_guilds(self) -> list[Guild]:
        """
        Get all guilds.

        Returns
        -------
        list[Guild]
            List of all guilds.
        """
        return await self.find_all()

    async def get_guild_count(self) -> int:
        """
        Get the total number of guilds.

        Returns
        -------
        int
            The total count of guilds.
        """
        return await self.count()

    # Additional methods that module files expect
    async def find_many(self, **filters: Any) -> list[Guild]:
        """
        Find many guilds with optional filters - alias for find_all.

        Parameters
        ----------
        **filters : Any
            Filter keyword arguments (currently unused, kept for API consistency).

        Returns
        -------
        list[Guild]
            List of guilds matching the filters.
        """
        return await self.find_all()

    async def insert_guild_by_id(self, guild_id: int, **kwargs: Any) -> Guild:
        """
        Insert a new guild by ID.

        Returns
        -------
        Guild
            The newly created guild.
        """
        return await self.create(id=guild_id, **kwargs)

    async def delete_guild_by_id(self, guild_id: int) -> bool:
        """
        Delete a guild by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(guild_id)
