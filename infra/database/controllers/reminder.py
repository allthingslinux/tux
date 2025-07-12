from datetime import datetime

from database.client import db
from database.controllers.base import BaseController

from prisma.actions import GuildActions
from prisma.models import Guild, Reminder


class ReminderController(BaseController[Reminder]):
    """Controller for managing user reminders.

    This controller provides methods for creating, retrieving, updating,
    and deleting reminders for users across guilds.
    """

    def __init__(self) -> None:
        """Initialize the ReminderController with the reminder table."""
        super().__init__("reminder")
        self.guild_table: GuildActions[Guild] = db.client.guild

    async def get_all_reminders(self) -> list[Reminder]:
        """Get all reminders across all guilds.

        Returns
        -------
        list[Reminder]
            List of all reminders
        """
        return await self.find_many(where={})

    async def get_reminder_by_id(self, reminder_id: int) -> Reminder | None:
        """Get a reminder by its ID.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to get

        Returns
        -------
        Reminder | None
            The reminder if found, None otherwise
        """
        return await self.find_unique(where={"reminder_id": reminder_id})

    async def insert_reminder(
        self,
        reminder_user_id: int,
        reminder_content: str,
        reminder_expires_at: datetime,
        reminder_channel_id: int,
        guild_id: int,
    ) -> Reminder:
        """Create a new reminder.

        Parameters
        ----------
        reminder_user_id : int
            The ID of the user to remind
        reminder_content : str
            The content of the reminder
        reminder_expires_at : datetime
            When the reminder should be sent
        reminder_channel_id : int
            The ID of the channel to send the reminder to
        guild_id : int
            The ID of the guild the reminder belongs to

        Returns
        -------
        Reminder
            The created reminder
        """
        return await self.create(
            data={
                "reminder_user_id": reminder_user_id,
                "reminder_content": reminder_content,
                "reminder_expires_at": reminder_expires_at,
                "reminder_channel_id": reminder_channel_id,
                "reminder_sent": False,
                "guild": self.connect_or_create_relation("guild_id", guild_id),
            },
            include={"guild": True},
        )

    async def delete_reminder_by_id(self, reminder_id: int) -> Reminder | None:
        """Delete a reminder by its ID.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to delete

        Returns
        -------
        Reminder | None
            The deleted reminder if found, None otherwise
        """
        return await self.delete(where={"reminder_id": reminder_id})

    async def update_reminder_by_id(
        self,
        reminder_id: int,
        reminder_content: str,
    ) -> Reminder | None:
        """Update a reminder's content.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to update
        reminder_content : str
            The new content for the reminder

        Returns
        -------
        Reminder | None
            The updated reminder if found, None otherwise
        """
        return await self.update(
            where={"reminder_id": reminder_id},
            data={"reminder_content": reminder_content},
        )

    async def update_reminder_status(self, reminder_id: int, sent: bool = True) -> Reminder | None:
        """Update the status of a reminder.

        This method sets the value "reminder_sent" to True by default.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to update
        sent : bool
            The new status of the reminder

        Returns
        -------
        Reminder | None
            The updated reminder if found, None otherwise
        """
        return await self.update(
            where={"reminder_id": reminder_id},
            data={"reminder_sent": sent},
        )

    async def get_reminders_by_user_id(
        self,
        user_id: int,
        include_sent: bool = False,
        limit: int | None = None,
    ) -> list[Reminder]:
        """Get all reminders for a user.

        Parameters
        ----------
        user_id : int
            The ID of the user to get reminders for
        include_sent : bool
            Whether to include reminders that have already been sent
        limit : int | None
            Optional limit on the number of reminders to return

        Returns
        -------
        list[Reminder]
            List of reminders for the user
        """
        where = {"reminder_user_id": user_id}
        if not include_sent:
            where["reminder_sent"] = False

        return await self.find_many(where=where, order={"reminder_expires_at": "asc"}, take=limit)

    async def get_reminders_by_guild_id(
        self,
        guild_id: int,
        include_sent: bool = False,
        limit: int | None = None,
    ) -> list[Reminder]:
        """Get all reminders for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to get reminders for
        include_sent : bool
            Whether to include reminders that have already been sent
        limit : int | None
            Optional limit on the number of reminders to return

        Returns
        -------
        list[Reminder]
            List of reminders for the guild
        """
        where = {"guild_id": guild_id}
        if not include_sent:
            where["reminder_sent"] = False

        return await self.find_many(where=where, order={"reminder_expires_at": "asc"}, take=limit)

    async def count_reminders_by_guild_id(self, guild_id: int, include_sent: bool = False) -> int:
        """Count the number of reminders in a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to count reminders for
        include_sent : bool
            Whether to include reminders that have already been sent

        Returns
        -------
        int
            The number of reminders in the guild
        """
        where = {"guild_id": guild_id}
        if not include_sent:
            where["reminder_sent"] = False

        return await self.count(where=where)

    async def bulk_delete_reminders_by_guild_id(self, guild_id: int) -> int:
        """Delete all reminders for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to delete reminders for

        Returns
        -------
        int
            The number of reminders deleted
        """
        return await self.delete_many(where={"guild_id": guild_id})

    async def mark_reminders_as_sent(self, reminder_ids: list[int]) -> int:
        """Mark multiple reminders as sent.

        Parameters
        ----------
        reminder_ids : list[int]
            The IDs of the reminders to mark as sent

        Returns
        -------
        int
            The number of reminders updated
        """
        return await self.update_many(where={"reminder_id": {"in": reminder_ids}}, data={"reminder_sent": True})
