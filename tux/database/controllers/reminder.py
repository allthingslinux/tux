from datetime import datetime

from prisma.models import Guild, Reminder
from tux.database.client import db


class ReminderController:
    def __init__(self) -> None:
        self.table = db.reminder
        self.guild_table = db.guild

    async def ensure_guild_exists(self, guild_id: int) -> Guild | None:
        guild = await self.guild_table.find_first(where={"guild_id": guild_id})
        if guild is None:
            return await self.guild_table.create(data={"guild_id": guild_id})
        return guild

    async def get_all_reminders(self) -> list[Reminder]:
        return await self.table.find_many()

    async def get_reminder_by_id(self, reminder_id: int) -> Reminder | None:
        return await self.table.find_first(where={"reminder_id": reminder_id})

    async def get_unsent_reminders(self) -> list[Reminder]:
        return await self.table.find_many(where={"reminder_sent": False})

    async def insert_reminder(
        self,
        reminder_user_id: int,
        reminder_content: str,
        reminder_expires_at: datetime,
        reminder_channel_id: int,
        guild_id: int,
    ) -> Reminder:
        await self.ensure_guild_exists(guild_id)

        return await self.table.create(
            data={
                "reminder_user_id": reminder_user_id,
                "reminder_content": reminder_content,
                "reminder_expires_at": reminder_expires_at,
                "reminder_channel_id": reminder_channel_id,
                "guild_id": guild_id,
                "reminder_sent": False,
            },
        )

    async def delete_reminder_by_id(self, reminder_id: int) -> None:
        await self.table.delete(where={"reminder_id": reminder_id})

    async def update_reminder_by_id(
        self,
        reminder_id: int,
        reminder_content: str,
    ) -> Reminder | None:
        return await self.table.update(
            where={"reminder_id": reminder_id},
            data={"reminder_content": reminder_content},
        )

    async def update_reminder_status(self, reminder_id: int, sent: bool = True) -> None:
        """
        Update the status of a reminder. This sets the value "reminder_sent" to True by default.

        Parameters
        ----------
        reminder_id : int
            The ID of the reminder to update.
        sent : bool
            The new status of the reminder.
        """
        await self.table.update(
            where={"reminder_id": reminder_id},
            data={"reminder_sent": sent},
        )
