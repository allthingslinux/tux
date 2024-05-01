from datetime import datetime

from prisma.models import Reminders
from tux.database.client import db


class RemindersController:
    def __init__(self) -> None:
        """
        Initializes the controller and connects to the reminders table in the database.
        """
        self.table = db.reminders

    async def get_all_reminders(self) -> list[Reminders]:
        """
        Retrieves all reminders from the database.

        Returns
        -------
        list[Reminders]
            A list of all reminders.
        """
        return await self.table.find_many()

    async def get_reminder_by_id(self, reminder_id: int) -> Reminders | None:
        """
        Retrieves a reminder from the database based on the specified reminder ID.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to retrieve.

        Returns
        -------
        Reminders or None
            The reminder if found, otherwise None.
        """
        return await self.table.find_first(where={"id": reminder_id})

    async def create_reminder(
        self,
        user_id: int,
        reminder_content: str,
        expires_at: datetime,
        channel_id: int,
        guild_id: int,
    ) -> Reminders:
        """
        Creates a new reminder in the database with the specified user ID, reminder content, expiration date, channel ID, and guild ID.

        Parameters
        ----------
        user_id : int
            The ID of the user for whom the reminder is created.
        reminder_content : str
            The content of the reminder.
        expires_at : datetime
            The expiration date and time of the reminder.
        channel_id : int
            The ID of the channel associated with the reminder.
        guild_id : int
            The ID of the guild associated with the reminder.

        Returns
        -------
        Reminders
            The newly created reminder.
        """
        return await self.table.create(
            data={
                "user_id": user_id,
                "content": reminder_content,
                "expires_at": expires_at,
                "channel_id": channel_id,
                "guild_id": guild_id,
            }
        )

    async def delete_reminder(self, reminder_id: int) -> None:
        """
        Deletes a reminder from the database based on the specified reminder ID.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to delete.

        Returns
        -------
        None
        """
        await self.table.delete(where={"id": reminder_id})

    async def update_reminder(self, reminder_id: int, reminder_content: str) -> Reminders | None:
        """
        Updates a reminder in the database with the specified reminder ID and new content.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to update.
        reminder_content : str
            The new content for the reminder.

        Returns
        -------
        Reminders or None
            The updated reminder if successful, or None if the reminder was not found.
        """
        return await self.table.update(
            where={"id": reminder_id},
            data={"content": reminder_content},
        )
