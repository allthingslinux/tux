"""
User level and XP tracking controller.

This controller manages Discord user experience points, levels, and ranking
information for guilds, supporting features like leveling systems and leaderboards.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import Levels

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class LevelsController(BaseController[Levels]):
    """Clean Levels controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the levels controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Levels, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_levels_by_member(
        self,
        member_id: int,
        guild_id: int,
    ) -> Levels | None:
        """
        Get levels for a specific member in a guild.

        Returns
        -------
        Levels | None
            The levels record if found, None otherwise.
        """
        return await self.find_one(
            filters=(Levels.member_id == member_id) & (Levels.guild_id == guild_id),
        )

    async def get_or_create_levels(self, member_id: int, guild_id: int) -> Levels:
        """
        Get levels for a member, or create them if they don't exist.

        Returns
        -------
        Levels
            The levels record for the member.
        """
        levels = await self.get_levels_by_member(member_id, guild_id)
        if levels is not None:
            return levels
        return await self.create(
            member_id=member_id,
            guild_id=guild_id,
            xp=0.0,
            level=0,
            blacklisted=False,
            last_message=datetime.now(UTC),
        )

    async def add_xp(self, member_id: int, guild_id: int, xp_amount: float) -> Levels:
        """
        Add XP to a member's levels.

        Returns
        -------
        Levels
            The updated levels record.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        new_xp = levels.xp + xp_amount
        new_level = int(new_xp**0.5)  # Simple level calculation

        return (
            await self.update_by_id(
                levels.member_id,
                xp=new_xp,
                level=new_level,
                last_message=datetime.now(UTC),
            )
            or levels
        )

    async def set_xp(self, member_id: int, guild_id: int, xp: float) -> Levels:
        """
        Set a member's XP to a specific value.

        Returns
        -------
        Levels
            The updated levels record.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        new_level = int(xp**0.5)

        return (
            await self.update_by_id(
                levels.member_id,
                xp=xp,
                level=new_level,
                last_message=datetime.now(UTC),
            )
            or levels
        )

    async def set_level(self, member_id: int, guild_id: int, level: int) -> Levels:
        """
        Set a member's level to a specific value.

        Returns
        -------
        Levels
            The updated levels record.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        xp = level**2  # Reverse level calculation

        return (
            await self.update_by_id(
                levels.member_id,
                xp=xp,
                level=level,
                last_message=datetime.now(UTC),
            )
            or levels
        )

    async def blacklist_member(self, member_id: int, guild_id: int) -> Levels:
        """
        Blacklist a member from gaining XP.

        Returns
        -------
        Levels
            The updated levels record.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return await self.update_by_id(levels.member_id, blacklisted=True) or levels

    async def unblacklist_member(self, member_id: int, guild_id: int) -> Levels:
        """
        Remove a member from the blacklist.

        Returns
        -------
        Levels
            The updated levels record.
        """
        levels = await self.get_levels_by_member(member_id, guild_id)
        if levels is None:
            return await self.get_or_create_levels(member_id, guild_id)
        return await self.update_by_id(levels.member_id, blacklisted=False) or levels

    async def get_top_members(self, guild_id: int, limit: int = 10) -> list[Levels]:
        """
        Get top members by XP in a guild.

        Returns
        -------
        list[Levels]
            List of top members sorted by XP (highest first).
        """
        # Use database-level sorting and limiting for better performance
        return await self.find_all(
            filters=Levels.guild_id == guild_id,
            order_by=[Levels.xp.desc()],  # type: ignore[attr-defined]
            limit=limit,
        )

    # Additional methods that module files expect
    async def get_xp(self, member_id: int, guild_id: int) -> float:
        """
        Get XP for a specific member in a guild.

        Returns
        -------
        float
            The member's XP value.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return levels.xp

    async def get_level(self, member_id: int, guild_id: int) -> int:
        """
        Get level for a specific member in a guild.

        Returns
        -------
        int
            The member's level.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return levels.level

    async def update_xp_and_level(
        self,
        member_id: int,
        guild_id: int,
        xp_amount: float | None = None,
        new_level: int | None = None,
        last_message: datetime | None = None,
        **kwargs: Any,
    ) -> Levels:
        """
        Update XP and level for a member.

        Returns
        -------
        Levels
            The updated levels record.

        Raises
        ------
        ValueError
            If xp_amount, new_level, or last_message is missing.
        """
        # Handle both positional and named parameter styles
        if xp_amount is None and "xp" in kwargs:
            xp_amount = kwargs["xp"]
        if new_level is None and "level" in kwargs:
            new_level = kwargs["level"]
        if last_message is None and "last_message" in kwargs:
            last_message = kwargs["last_message"]

        if xp_amount is None or new_level is None or last_message is None:
            error_msg = "xp_amount, new_level, and last_message are required"
            raise ValueError(error_msg)

        # Use composite key for update
        await self.update_where(
            (Levels.member_id == member_id) & (Levels.guild_id == guild_id),
            {"xp": xp_amount, "level": new_level, "last_message": last_message},
        )
        # Return updated record
        return await self.get_or_create_levels(member_id, guild_id)

    async def reset_xp(self, member_id: int, guild_id: int) -> Levels:
        """
        Reset XP and level for a member.

        Returns
        -------
        Levels
            The updated levels record with XP and level reset to 0.
        """
        # Use composite key for update
        await self.update_where(
            (Levels.member_id == member_id) & (Levels.guild_id == guild_id),
            {"xp": 0.0, "level": 0},
        )
        # Return updated record
        return await self.get_or_create_levels(member_id, guild_id)

    async def toggle_blacklist(self, member_id: int, guild_id: int) -> bool:
        """
        Toggle blacklist status for a member.

        Returns
        -------
        bool
            The new blacklist status.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        new_status = not levels.blacklisted
        # Use composite key for update
        await self.update_where(
            (Levels.member_id == member_id) & (Levels.guild_id == guild_id),
            {"blacklisted": new_status},
        )
        return new_status

    # Additional methods that module files expect
    async def is_blacklisted(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is blacklisted.

        Returns
        -------
        bool
            True if member is blacklisted, False otherwise.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return levels.blacklisted

    async def get_last_message_time(self, member_id: int, guild_id: int) -> datetime:
        """
        Get the last message time for a member.

        Returns
        -------
        datetime
            The timestamp of the member's last message.
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return levels.last_message

    async def get_xp_and_level(
        self,
        member_id: int,
        guild_id: int,
    ) -> tuple[float, int]:
        """
        Get both XP and level for a member.

        Returns
        -------
        tuple[float, int]
            A tuple containing (xp, level).
        """
        levels = await self.get_or_create_levels(member_id, guild_id)
        return levels.xp, levels.level

    async def get_user_level_data(
        self,
        member_id: int,
        guild_id: int,
    ) -> Levels | None:
        """
        Get complete level data for a user in a single query.

        This method is optimized for batch fetching user level data including
        XP, level, blacklist status, and last message time in one database call.

        Returns
        -------
        Levels | None
            The levels record if found, None otherwise.
        """
        return await self.get_levels_by_member(member_id, guild_id)

    async def get_member_rank(self, member_id: int, guild_id: int) -> int:
        """
        Get a member's rank in their guild (1-based).

        Returns
        -------
        int
            The member's rank (1 = highest XP), or -1 if blacklisted/not found.
        """
        levels = await self.get_levels_by_member(member_id, guild_id)
        if levels is None or levels.blacklisted:
            return -1

        # Count members with higher XP
        higher_count = await self.count(
            filters=(Levels.guild_id == guild_id)
            & (not Levels.blacklisted)
            & (Levels.xp > levels.xp),
        )
        return higher_count + 1

    async def get_guild_stats(self, guild_id: int) -> dict[str, Any]:
        """
        Get guild statistics.

        Returns
        -------
        dict[str, Any]
            Dictionary containing total_members, blacklisted_count, and active_members.
        """
        total_members = await self.count(filters=Levels.guild_id == guild_id)
        blacklisted_count = await self.count(
            filters=(Levels.guild_id == guild_id) & (Levels.blacklisted),
        )
        active_members = total_members - blacklisted_count

        return {
            "total_members": total_members,
            "blacklisted_count": blacklisted_count,
            "active_members": active_members,
        }
