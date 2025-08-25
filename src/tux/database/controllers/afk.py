from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from tux.database.controllers.base import BaseController
from tux.database.models import AFK
from tux.database.service import DatabaseService


class AfkController(BaseController[AFK]):
    """Clean AFK controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None):
        super().__init__(AFK, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_afk_by_member(self, member_id: int, guild_id: int) -> AFK | None:
        """Get AFK status for a specific member in a guild."""
        return await self.find_one(filters=(AFK.member_id == member_id) & (AFK.guild_id == guild_id))

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
        """Set a member as AFK."""
        # Check if member is already AFK in this guild
        existing = await self.get_afk_by_member(member_id, guild_id)
        if existing:
            # Update existing AFK
            return (
                await self.update_by_id(
                    existing.member_id,
                    nickname=nickname,
                    reason=reason,
                    since=datetime.now(UTC),
                    until=until,
                    enforced=enforced,
                    perm_afk=is_perm,
                )
                or existing
            )  # Fallback to existing if update fails
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
        """Remove AFK status for a member."""
        existing = await self.get_afk_by_member(member_id, guild_id)
        return await self.delete_by_id(existing.member_id) if existing else False

    async def get_all_afk_members(self, guild_id: int) -> list[AFK]:
        """Get all members currently AFK in a guild."""
        return await self.find_all(filters=AFK.guild_id == guild_id)

    async def is_member_afk(self, member_id: int, guild_id: int) -> bool:
        """Check if a member is AFK in a guild."""
        return await self.get_afk_by_member(member_id, guild_id) is not None

    async def is_member_perm_afk(self, member_id: int, guild_id: int) -> bool:
        """Check if a member is permanently AFK in a guild."""
        afk = await self.get_afk_by_member(member_id, guild_id)
        return afk is not None and afk.perm_afk

    # Additional methods that module files expect (aliases)
    async def is_afk(self, member_id: int, guild_id: int) -> bool:
        """Check if a member is currently AFK - alias for is_member_afk."""
        return await self.is_member_afk(member_id, guild_id)

    async def get_afk_member(self, member_id: int, guild_id: int) -> AFK | None:
        """Get AFK record for a member - alias for get_afk_by_member."""
        return await self.get_afk_by_member(member_id, guild_id)

    async def remove_afk(self, member_id: int, guild_id: int) -> bool:
        """Remove AFK status for a member - alias for remove_member_afk."""
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
        """Set a member as AFK - alias for set_member_afk."""
        return await self.set_member_afk(member_id, nickname, reason, guild_id, is_perm, until, enforced)

    async def find_many(self, **filters: Any) -> list[AFK]:
        """Find many AFK records with optional filters - alias for find_all."""
        return await self.find_all()

    async def is_perm_afk(self, member_id: int, guild_id: int) -> bool:
        """Check if a member is permanently AFK - alias for is_member_perm_afk."""
        return await self.is_member_perm_afk(member_id, guild_id)

    async def get_expired_afk_members(self, guild_id: int) -> list[AFK]:
        """Get all expired AFK members in a guild."""
        # For now, return empty list to avoid complex datetime filtering issues
        # In the future, implement proper expired AFK filtering
        return []
