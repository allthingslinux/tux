from typing import Any

from database.controllers.base import BaseController

from prisma.models import Guild


class GuildController(BaseController[Guild]):
    """Controller for managing guild records.

    This controller provides methods for managing guild records in the database.
    It inherits common CRUD operations from BaseController.
    """

    def __init__(self):
        """Initialize the GuildController with the guild table."""
        super().__init__("guild")
        # Type hint for better IDE support
        self.table: Any = self.table

    async def get_guild_by_id(self, guild_id: int) -> Guild | None:
        """Get a guild by its ID.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get

        Returns
        -------
        Guild | None
            The guild if found, None otherwise
        """
        return await self.find_one(where={"guild_id": guild_id})

    async def get_or_create_guild(self, guild_id: int) -> Guild:
        """Get an existing guild or create it if it doesn't exist.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get or create

        Returns
        -------
        Guild
            The existing or newly created guild
        """
        return await self.table.upsert(
            where={"guild_id": guild_id},
            data={
                "create": {"guild_id": guild_id},
                "update": {},
            },
        )

    async def insert_guild_by_id(self, guild_id: int) -> Guild:
        """Insert a new guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to insert

        Returns
        -------
        Guild
            The created guild
        """
        return await self.create(data={"guild_id": guild_id})

    async def delete_guild_by_id(self, guild_id: int) -> None:
        """Delete a guild by its ID.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete
        """
        await self.delete(where={"guild_id": guild_id})

    async def get_all_guilds(self) -> list[Guild]:
        """Get all guilds.

        Returns
        -------
        list[Guild]
            List of all guilds
        """
        return await self.find_many(where={})
