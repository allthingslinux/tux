import datetime

from loguru import logger

from prisma.models import Guild
from tux.database.client import db


class LevelsController:
    def __init__(self) -> None:
        self.guild = db.guild
        self.levels_table = db.levels

    async def ensure_guild_exists(self, guild_id: int) -> Guild:
        """
        Ensure the guild exists in the database.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        Guild
            The guild object.
        """
        guild = await self.guild.find_first(where={"guild_id": guild_id})
        if guild is None:
            guild = await self.guild.create(data={"guild_id": guild_id})
        return guild

    async def get_xp(self, member_id: int, guild_id: int) -> float:
        """
        Get the XP of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        float
            The XP of the member.
        """
        await self.ensure_guild_exists(guild_id)
        try:
            xp = await self.levels_table.find_first(where={"member_id": member_id, "guild_id": guild_id})
        except Exception as e:
            logger.error(f"Error querying XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0.0
        else:
            return xp.xp if xp else 0.0

    async def get_level(self, member_id: int, guild_id: int) -> int:
        """
        Get the level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        int
            The level of the member.
        """
        await self.ensure_guild_exists(guild_id)
        try:
            level = await self.levels_table.find_first(where={"member_id": member_id, "guild_id": guild_id})
        except Exception as e:
            logger.error(f"Error querying level for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0
        else:
            return level.level if level else 0

    async def get_last_message_time(self, member_id: int, guild_id: int) -> datetime.datetime | None:
        """
        Get the last message time of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        datetime.datetime | None
            The last message time of the member, or None if not found.
        """
        await self.ensure_guild_exists(guild_id)
        try:
            level = await self.levels_table.find_first(where={"member_id": member_id, "guild_id": guild_id})
        except Exception as e:
            logger.error(f"Error querying last message time for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return None
        else:
            return level.last_message if level else None

    async def is_blacklisted(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is blacklisted in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        bool
            True if the member is blacklisted, False otherwise.
        """
        await self.ensure_guild_exists(guild_id)
        try:
            blacklisted = await self.levels_table.find_first(where={"member_id": member_id, "guild_id": guild_id})
        except Exception as e:
            logger.error(f"Error querying blacklist status for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return False
        else:
            return blacklisted.blacklisted if blacklisted else False

    async def update_xp_and_level(
        self,
        member_id: int,
        guild_id: int,
        xp: float,
        level: int,
        last_message: datetime.datetime,
    ) -> None:
        """
        Update the XP and level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        xp : float
            The XP of the member.
        level : int
            The level of the member.
        last_message : datetime.datetime
            The last message time of the member.

        Returns
        -------
        None
        """
        await self.ensure_guild_exists(guild_id)
        try:
            await self.levels_table.upsert(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={
                    "create": {
                        "member_id": member_id,
                        "guild_id": guild_id,
                        "xp": xp,
                        "level": level,
                        "last_message": last_message,
                    },
                    "update": {"xp": xp, "level": level, "last_message": last_message},
                },
            )
        except Exception as e:
            logger.error(f"Error updating XP and level for member_id: {member_id}, guild_id: {guild_id}: {e}")

    async def toggle_blacklist(self, member_id: int, guild_id: int) -> bool:
        """
        Toggle the blacklist status of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        bool
            The new blacklist status of the member.
        """
        await self.ensure_guild_exists(guild_id)
        try:
            levels = await self.levels_table.find_first(where={"member_id": member_id, "guild_id": guild_id})
            if levels is None:
                await self.levels_table.create(data={"member_id": member_id, "guild_id": guild_id, "blacklisted": True})
                return True
            new_blacklist_status = not levels.blacklisted
            await self.levels_table.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"blacklisted": new_blacklist_status},
            )
        except Exception as e:
            logger.error(f"Error toggling blacklist for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return False
        else:
            return new_blacklist_status

    async def reset_xp(self, member_id: int, guild_id: int) -> None:
        """
        Reset the XP and level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        None
        """
        await self.ensure_guild_exists(guild_id)
        try:
            await self.levels_table.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"xp": 0.0, "level": 0},
            )
        except Exception as e:
            logger.error(f"Error resetting XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
