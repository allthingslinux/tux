from datetime import UTC, datetime

from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.models import AFKModel, Guild


class AfkController(BaseController[AFKModel]):
    """Controller for managing AFK status records.

    This controller provides methods for tracking, checking, and managing
    AFK (Away From Keyboard) status of guild members.
    """

    def __init__(self) -> None:
        """Initialize the AfkController with the afkmodel table."""
        super().__init__("afkmodel")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_afk_member(self, member_id: int, *, guild_id: int) -> AFKModel | None:
        """Get the AFK record for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member to check
        guild_id : int
            The ID of the guild to check in

        Returns
        -------
        AFKModel | None
            The AFK record if found, None otherwise
        """
        return await self.find_one(where={"member_id": member_id, "guild_id": guild_id})

    async def is_afk(self, member_id: int, *, guild_id: int) -> bool:
        """Check if a member is AFK in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member to check
        guild_id : int
            The ID of the guild to check in

        Returns
        -------
        bool
            True if the member is AFK, False otherwise
        """
        entry = await self.get_afk_member(member_id, guild_id=guild_id)
        return entry is not None

    async def is_perm_afk(self, member_id: int, *, guild_id: int) -> bool:
        """Check if a member is permanently AFK in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member to check
        guild_id : int
            The ID of the guild to check in

        Returns
        -------
        bool
            True if the member is permanently AFK, False otherwise
        """
        is_user_perm_afk = await self.find_one(
            where={"member_id": member_id, "guild_id": guild_id, "perm_afk": True},
        )
        return is_user_perm_afk is not None

    async def set_afk(
        self,
        member_id: int,
        nickname: str,
        reason: str,
        guild_id: int,
        perm_afk: bool = False,
        until: datetime | None = None,
        enforced: bool = False,
    ) -> AFKModel:
        """Insert or update an AFK record for a member.

        Parameters
        ----------
        member_id : int
            The ID of the member to set as AFK
        nickname : str
            The nickname of the member
        reason : str
            The reason for being AFK
        guild_id : int
            The ID of the guild
        perm_afk : bool
            Whether the AFK status is permanent

        Returns
        -------
        AFKModel
            The created or updated AFK record
        """
        create_data = {
            "member_id": member_id,
            "nickname": nickname,
            "reason": reason,
            "perm_afk": perm_afk,
            "guild": self.connect_or_create_relation("guild_id", guild_id),
            "until": until,
            "enforced": enforced,
            "since": datetime.now(UTC),
        }
        update_data = {
            "nickname": nickname,
            "reason": reason,
            "perm_afk": perm_afk,
            "until": until,
            "enforced": enforced,
            "since": datetime.now(UTC),
        }

        return await self.upsert(
            where={"member_id": member_id},
            create=create_data,
            update=update_data,
            include={"guild": True},
        )

    async def remove_afk(self, member_id: int) -> AFKModel | None:
        """Remove an AFK record for a member.

        Parameters
        ----------
        member_id : int
            The ID of the member to remove AFK status from

        Returns
        -------
        AFKModel | None
            The deleted AFK record if found, None otherwise
        """
        return await self.delete(where={"member_id": member_id})

    async def count_afk_members(self, guild_id: int) -> int:
        """Count the number of AFK members in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count AFK members for

        Returns
        -------
        int
            The number of AFK members in the guild
        """
        return await self.count(where={"guild_id": guild_id})

    async def get_all_afk_members(self, guild_id: int) -> list[AFKModel]:
        """Get all AFK members in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get AFK members for

        Returns
        -------
        list[AFKModel]
            List of AFK members in the guild
        """
        return await self.find_many(where={"guild_id": guild_id})
