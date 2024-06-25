from datetime import datetime

from prisma.models import Reminder
from tux.database.client import db


class ReminderController:
    def __init__(self) -> None:
        self.table = db.reminder

    async def get_all_reminders(self) -> list[Reminder]:
        return await self.table.find_many()

    async def get_reminder_by_id(self, reminder_id: int) -> Reminder | None:
        return await self.table.find_first(where={"reminder_id": reminder_id})

    async def insert_reminder(
        self,
        reminder_user_id: int,
        reminder_content: str,
        reminder_expires_at: datetime,
        reminder_channel_id: int,
        guild_id: int,
    ) -> Reminder:
        return await self.table.create(
            data={
                "reminder_user_id": reminder_user_id,
                "reminder_content": reminder_content,
                "reminder_expires_at": reminder_expires_at,
                "reminder_channel_id": reminder_channel_id,
                "guild_id": guild_id,
            }
        )

    async def delete_reminder_by_id(self, reminder_id: int) -> None:
        await self.table.delete(where={"reminder_id": reminder_id})

    async def update_reminder_by_id(self, reminder_id: int, reminder_content: str) -> Reminder | None:
        return await self.table.update(
            where={"reminder_id": reminder_id},
            data={"reminder_content": reminder_content},
        )
