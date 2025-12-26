"""
User reminder scheduling controller.

This controller manages scheduled reminders for Discord users, allowing them
to set timed notifications and messages to be delivered at specified times.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from tux.database.controllers.base import BaseController
from tux.database.models import Reminder

if TYPE_CHECKING:
    from tux.database.service import DatabaseService


class ReminderController(BaseController[Reminder]):
    """Clean Reminder controller using the new BaseController pattern."""

    def __init__(self, db: DatabaseService | None = None) -> None:
        """Initialize the reminder controller.

        Parameters
        ----------
        db : DatabaseService | None, optional
            The database service instance. If None, uses the default service.
        """
        super().__init__(Reminder, db)

    # Simple, clean methods that use BaseController's CRUD operations
    async def get_reminder_by_id(self, reminder_id: int) -> Reminder | None:
        """
        Get a reminder by its ID.

        Returns
        -------
        Reminder | None
            The reminder if found, None otherwise.
        """
        return await self.get_by_id(reminder_id)

    async def get_reminders_by_user(
        self,
        user_id: int,
        guild_id: int,
    ) -> list[Reminder]:
        """
        Get all reminders for a specific user in a guild.

        Returns
        -------
        list[Reminder]
            List of all reminders for the user in the guild.
        """
        return await self.find_all(
            filters=(Reminder.reminder_user_id == user_id)
            & (Reminder.guild_id == guild_id),
        )

    async def get_reminders_by_guild(self, guild_id: int) -> list[Reminder]:
        """
        Get all reminders in a guild.

        Returns
        -------
        list[Reminder]
            List of all reminders for the guild.
        """
        return await self.find_all(filters=Reminder.guild_id == guild_id)

    async def create_reminder(
        self,
        user_id: int,
        guild_id: int,
        channel_id: int,
        message: str,
        expires_at: datetime,
        **kwargs: Any,
    ) -> Reminder:
        """
        Create a new reminder.

        Returns
        -------
        Reminder
            The newly created reminder.
        """
        return await self.create(
            reminder_user_id=user_id,
            guild_id=guild_id,
            reminder_channel_id=channel_id,
            reminder_content=message,
            reminder_expires_at=expires_at,
            **kwargs,
        )

    async def update_reminder(self, reminder_id: int, **kwargs: Any) -> Reminder | None:
        """
        Update a reminder by ID.

        Returns
        -------
        Reminder | None
            The updated reminder, or None if not found.
        """
        return await self.update_by_id(reminder_id, **kwargs)

    async def delete_reminder(self, reminder_id: int) -> bool:
        """
        Delete a reminder by ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(reminder_id)

    async def get_expired_reminders(self) -> list[Reminder]:
        """
        Get all expired reminders.

        Returns
        -------
        list[Reminder]
            List of all expired reminders.
        """
        return await self.find_all(
            filters=Reminder.reminder_expires_at <= datetime.now(UTC),
        )

    async def get_active_reminders(self, guild_id: int) -> list[Reminder]:
        """
        Get all active (non-expired) reminders in a guild.

        Returns
        -------
        list[Reminder]
            List of active reminders.
        """
        return await self.find_all(
            filters=(Reminder.guild_id == guild_id)
            & (Reminder.reminder_expires_at > datetime.now(UTC)),
        )

    async def get_reminders_by_channel(self, channel_id: int) -> list[Reminder]:
        """
        Get all reminders for a specific channel.

        Returns
        -------
        list[Reminder]
            List of reminders for the channel.
        """
        return await self.find_all(filters=Reminder.reminder_channel_id == channel_id)

    async def get_reminder_count_by_user(self, user_id: int, guild_id: int) -> int:
        """
        Get the number of reminders for a user in a guild.

        Returns
        -------
        int
            The count of reminders for the user.
        """
        return await self.count(
            filters=(Reminder.reminder_user_id == user_id)
            & (Reminder.guild_id == guild_id),
        )

    async def get_reminder_count_by_guild(self, guild_id: int) -> int:
        """
        Get the total number of reminders in a guild.

        Returns
        -------
        int
            The total count of reminders in the guild.
        """
        return await self.count(filters=Reminder.guild_id == guild_id)

    # Additional methods that module files expect
    async def delete_reminder_by_id(self, reminder_id: int) -> bool:
        """
        Delete a reminder by its ID.

        Returns
        -------
        bool
            True if deleted successfully, False otherwise.
        """
        return await self.delete_by_id(reminder_id)

    async def get_all_reminders(self, guild_id: int) -> list[Reminder]:
        """
        Get all reminders in a guild.

        Returns
        -------
        list[Reminder]
            List of all reminders for the guild.
        """
        return await self.find_all(filters=Reminder.guild_id == guild_id)

    async def insert_reminder(self, **kwargs: Any) -> Reminder:
        """
        Insert a new reminder - alias for create.

        Returns
        -------
        Reminder
            The newly created reminder.
        """
        return await self.create(**kwargs)

    async def cleanup_expired_reminders(self) -> int:
        """
        Delete all expired reminders and return the count.

        Returns
        -------
        int
            The number of reminders that were deleted.
        """
        expired = await self.get_expired_reminders()
        count = 0
        for reminder in expired:
            if await self.delete_by_id(reminder.id):
                count += 1
        return count
