"""
AFK (Away From Keyboard) status management controller.

This controller manages AFK status for Discord guild members, including
temporary and permanent AFK states with customizable messages and time limits.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import AFK

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class AfkController(BaseController[AFK]):
    """Clean AFK controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the AFK controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(AFK, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_afk_by_member(self, member_id: int, guild_id: int) -> AFK | None:
        """
        Get AFK status for a specific member in a guild.

        Returns
        -------
        AFK | None
            The AFK record if found, None otherwise.
        """
        return await self.find_one(
            filters=(AFK.member_id == member_id) & (AFK.guild_id == guild_id),
        )

    async def set_member_afk(
        self,
        member_id: int,
        nickname: str,
        reason: str,
        guild_id: int,
        is_perm: bool = False,
        until: datetime | None = None,
        enforced: bool = False,
    ) -> AFK:
        """
        Set a member as AFK.

        Returns
        -------
        AFK
            The AFK record (created or updated).
        """
        # Check if member is already AFK in this guild
        existing = await self.get_afk_by_member(member_id, guild_id)
        if existing:
            # Update existing AFK using composite primary key
            updated = await self.update_by_id(
                (member_id, guild_id),
                nickname=nickname,
                reason=reason,
                since=datetime.now(UTC),
                until=until,
                enforced=enforced,
                perm_afk=is_perm,
            )
            return updated if updated is not None else existing
        # Create new AFK
        return await self.create(
            member_id=member_id,
            nickname=nickname,
            reason=reason,
            guild_id=guild_id,
            since=datetime.now(UTC),
            until=until,
            enforced=enforced,
            perm_afk=is_perm,
        )

    async def remove_member_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Remove AFK status for a member.

        Returns
        -------
        bool
            True if removed successfully, False otherwise.
        """
        existing = await self.get_afk_by_member(member_id, guild_id)
        return (
            await self.delete_by_id((existing.member_id, existing.guild_id))
            if existing
            else False
        )

    async def get_all_afk_members(self, guild_id: int) -> list[AFK]:
        """
        Get all members currently AFK in a guild.

        Returns
        -------
        list[AFK]
            List of all AFK records for the guild.
        """
        return await self.find_all(filters=AFK.guild_id == guild_id)

    async def is_member_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is AFK in a guild.

        Returns
        -------
        bool
            True if member is AFK, False otherwise.
        """
        return await self.get_afk_by_member(member_id, guild_id) is not None

    async def is_member_perm_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is permanently AFK in a guild.

        Returns
        -------
        bool
            True if member is permanently AFK, False otherwise.
        """
        afk = await self.get_afk_by_member(member_id, guild_id)
        return afk is not None and afk.perm_afk

    # Additional methods that module files expect (aliases)
    async def is_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is currently AFK - alias for is_member_afk.

        Returns
        -------
        bool
            True if member is AFK, False otherwise.
        """
        return await self.is_member_afk(member_id, guild_id)

    async def get_afk_member(self, member_id: int, guild_id: int) -> AFK | None:
        """
        Get AFK record for a member - alias for get_afk_by_member.

        Returns
        -------
        AFK | None
            The AFK record if found, None otherwise.
        """
        return await self.get_afk_by_member(member_id, guild_id)

    async def remove_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Remove AFK status for a member - alias for remove_member_afk.

        Returns
        -------
        bool
            True if removed successfully, False otherwise.
        """
        return await self.remove_member_afk(member_id, guild_id)

    # Additional methods that module files expect
    async def set_afk(
        self,
        member_id: int,
        nickname: str,
        reason: str,
        guild_id: int,
        is_perm: bool,
        until: datetime | None = None,
        enforced: bool = False,
    ) -> AFK:
        """
        Set a member as AFK - alias for set_member_afk.

        Returns
        -------
        AFK
            The AFK record (created or updated).
        """
        return await self.set_member_afk(
            member_id,
            nickname,
            reason,
            guild_id,
            is_perm,
            until,
            enforced,
        )

    async def find_many(
        self,
        where: dict[str, Any] | None = None,
        **filters: Any,
    ) -> list[AFK]:
        """
        Find many AFK records with optional filters - alias for find_all.

        Parameters
        ----------
        where : dict[str, Any] | None, optional
            Filter criteria as a dictionary (e.g., {"guild_id": 123}).
        **filters : Any
            Additional filter criteria as keyword arguments.

        Returns
        -------
        list[AFK]
            List of AFK records matching the filters.
        """
        # Combine where dict with additional filters
        combined_filters = dict(where) if where else {}
        combined_filters.update(filters)

        if not combined_filters:
            return await self.find_all()

        # Build filter expression from combined filters
        filter_expr = None
        for key, value in combined_filters.items():
            if hasattr(AFK, key):
                attr_filter = getattr(AFK, key) == value
                filter_expr = (
                    attr_filter if filter_expr is None else filter_expr & attr_filter
                )

        return (
            await self.find_all(filters=filter_expr)
            if filter_expr
            else await self.find_all()
        )

    async def is_perm_afk(self, member_id: int, guild_id: int) -> bool:
        """
        Check if a member is permanently AFK - alias for is_member_perm_afk.

        Returns
        -------
        bool
            True if member is permanently AFK, False otherwise.
        """
        return await self.is_member_perm_afk(member_id, guild_id)

    async def get_expired_afk_members(self, guild_id: int) -> list[AFK]:
        """
        Get all expired AFK members in a guild.

        Returns expired AFK entries where:
        - until is not NULL
        - until is in the past
        - perm_afk is False (temporary AFK only)

        Parameters
        ----------
        guild_id : int
            The guild ID to check for expired AFK entries.

        Returns
        -------
        list[AFK]
            List of expired AFK records.
        """
        now = datetime.now(UTC)
        return await self.find_all(
            filters=(
                (AFK.guild_id == guild_id)
                & (AFK.perm_afk == False)  # noqa: E712 - Temporary AFK only
                & (AFK.until.is_not(None))  # type: ignore[attr-defined]
                & (AFK.until < now)  # type: ignore[arg-type]
            ),
        )
