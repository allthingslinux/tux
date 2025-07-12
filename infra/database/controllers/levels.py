import datetime
import math

from database.client import db
from database.controllers.base import BaseController
from loguru import logger

from prisma.actions import GuildActions
from prisma.models import Guild, Levels


class LevelsController(BaseController[Levels]):
    """Controller for managing user levels and experience.

    This controller provides methods for tracking, updating, and querying
    user levels and experience points across guilds.
    """

    def __init__(self) -> None:
        """Initialize the LevelsController with the levels table."""
        super().__init__("levels")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_xp(self, member_id: int, guild_id: int) -> float:
        """Get the XP of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        float
            The XP of the member, or 0.0 if not found
        """
        try:
            levels = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})
            return self.safe_get_attr(levels, "xp", 0.0)
        except Exception as e:
            logger.error(f"Error querying XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0.0

    async def get_level(self, member_id: int, guild_id: int) -> int:
        """Get the level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The level of the member, or 0 if not found
        """
        try:
            levels = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})
            return self.safe_get_attr(levels, "level", 0)
        except Exception as e:
            logger.error(f"Error querying level for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0

    async def get_xp_and_level(self, member_id: int, guild_id: int) -> tuple[float, int]:
        """Get the XP and level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        tuple[float, int]
            A tuple containing the XP and level of the member, or (0.0, 0) if not found
        """
        try:
            record = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})

            if record:
                return (self.safe_get_attr(record, "xp", 0.0), self.safe_get_attr(record, "level", 0))
            return (0.0, 0)  # noqa: TRY300

        except Exception as e:
            logger.error(f"Error querying XP and level for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return (0.0, 0)

    async def get_last_message_time(self, member_id: int, guild_id: int) -> datetime.datetime | None:
        """Get the last message time of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        datetime.datetime | None
            The last message time of the member, or None if not found
        """
        try:
            levels = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})
            return self.safe_get_attr(levels, "last_message", None)
        except Exception as e:
            logger.error(f"Error querying last message time for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return None

    async def is_blacklisted(self, member_id: int, guild_id: int) -> bool:
        """Check if a member is blacklisted in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        bool
            True if the member is blacklisted, False otherwise
        """
        try:
            levels = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})
            return self.safe_get_attr(levels, "blacklisted", False)
        except Exception as e:
            logger.error(f"Error querying blacklist status for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return False

    async def update_xp_and_level(
        self,
        member_id: int,
        guild_id: int,
        xp: float,
        level: int,
        last_message: datetime.datetime,
    ) -> Levels | None:
        """Update the XP and level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild
        xp : float
            The XP of the member
        level : int
            The level of the member
        last_message : datetime.datetime
            The last message time of the member

        Returns
        -------
        Levels | None
            The updated levels record, or None if the update failed
        """
        try:
            return await self.upsert(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                create={
                    "member_id": member_id,
                    "xp": xp,
                    "level": level,
                    "last_message": last_message,
                    "guild": self.connect_or_create_relation("guild_id", guild_id),
                },
                update={"xp": xp, "level": level, "last_message": last_message},
            )
        except Exception as e:
            logger.error(f"Error updating XP and level for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return None

    async def toggle_blacklist(self, member_id: int, guild_id: int) -> bool:
        """Toggle the blacklist status of a member in a guild.

        This method uses a transaction to ensure atomicity.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        bool
            The new blacklist status of the member
        """

        async def toggle_tx():
            try:
                levels = await self.find_one(where={"member_id": member_id, "guild_id": guild_id})

                if levels is None:
                    # Create new record with blacklisted=True
                    await self.create(
                        data={
                            "member_id": member_id,
                            "blacklisted": True,
                            "xp": 0.0,
                            "level": 0,
                            "guild": self.connect_or_create_relation("guild_id", guild_id),
                        },
                    )
                    return True

                # Toggle existing record's blacklisted status
                current_status = self.safe_get_attr(levels, "blacklisted", False)
                new_status = not current_status

                await self.update(
                    where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                    data={"blacklisted": new_status},
                )

                return new_status  # noqa: TRY300
            except Exception as e:
                logger.error(f"Error toggling blacklist for member_id: {member_id}, guild_id: {guild_id}: {e}")
                return False

        return await self.execute_transaction(toggle_tx)

    async def reset_xp(self, member_id: int, guild_id: int) -> Levels | None:
        """Reset the XP and level of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        Levels | None
            The updated levels record, or None if the update failed
        """
        try:
            result = await self.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"xp": 0.0, "level": 0},
            )
        except Exception as e:
            logger.error(f"Error resetting XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return None
        else:
            return result

    async def get_top_members(self, guild_id: int, limit: int = 10, skip: int = 0) -> list[Levels]:
        """Get the top members in a guild by XP.

        Parameters
        ----------
        guild_id : int
            The ID of the guild
        limit : int
            The maximum number of members to return
        skip : int
            The number of members to skip

        Returns
        -------
        list[Levels]
            The top members in the guild by XP
        """
        try:
            return await self.find_many(
                where={"guild_id": guild_id, "blacklisted": False},
                order={"xp": "desc"},
                take=limit,
                skip=skip,
            )
        except Exception as e:
            logger.error(f"Error querying top members for guild_id: {guild_id}: {e}")
            return []

    async def add_xp(self, member_id: int, guild_id: int, xp_to_add: float) -> tuple[float, int, bool]:
        """Add XP to a member and calculate if they leveled up.

        This method uses a transaction to ensure atomicity.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild
        xp_to_add : float
            The amount of XP to add

        Returns
        -------
        tuple[float, int, bool]
            A tuple containing the new XP, new level, and whether the member leveled up
        """

        async def add_xp_tx():
            # Initialize with defaults in case of failure
            current_xp = 0.0
            current_level = 0

            try:
                # Get current XP and level
                current_xp, current_level = await self.get_xp_and_level(member_id, guild_id)

                # Calculate new XP and level
                new_xp = current_xp + xp_to_add
                new_level = self.calculate_level(new_xp)
                leveled_up = new_level > current_level

                # Update database
                now = datetime.datetime.now(datetime.UTC)
                await self.update_xp_and_level(
                    member_id=member_id,
                    guild_id=guild_id,
                    xp=new_xp,
                    level=new_level,
                    last_message=now,
                )
            except Exception as e:
                logger.error(f"Error adding XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
                return (current_xp, current_level, False)
            else:
                return (new_xp, new_level, leveled_up)

        return await self.execute_transaction(add_xp_tx)

    @staticmethod
    def calculate_level(xp: float) -> int:
        """Calculate level based on XP.

        This uses a standard RPG-style level curve.

        Parameters
        ----------
        xp : float
            The XP to calculate the level from

        Returns
        -------
        int
            The calculated level
        """
        # Base calculation: level = floor(sqrt(xp / 100))

        return math.floor(math.sqrt(xp / 100))

    async def count_ranked_members(self, guild_id: int) -> int:
        """Count the number of ranked members in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The number of ranked members
        """
        return await self.count(where={"guild_id": guild_id, "blacklisted": False})

    async def get_rank(self, member_id: int, guild_id: int) -> int:
        """Get the rank of a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The rank of the member (1-based), or 0 if not found
        """
        try:
            # Get the member's XP
            member_xp = await self.get_xp(member_id, guild_id)

            # Count members with more XP
            higher_ranked = await self.count(
                where={
                    "guild_id": guild_id,
                    "blacklisted": False,
                    "xp": {"gt": member_xp},
                },
            )

            # Rank is position (1-based)
            return higher_ranked + 1
        except Exception as e:
            logger.error(f"Error getting rank for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0

    async def bulk_delete_by_guild_id(self, guild_id: int) -> int:
        """Delete all levels data for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild

        Returns
        -------
        int
            The number of records deleted
        """
        return await self.delete_many(where={"guild_id": guild_id})
