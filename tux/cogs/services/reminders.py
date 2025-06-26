import asyncio
import contextlib
import datetime
import heapq
from collections.abc import Coroutine
from typing import Any, NamedTuple

import discord
from discord.ext import commands, tasks
from loguru import logger

from prisma.models import Reminder
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator


class ScheduledReminder(NamedTuple):
    """A scheduled reminder entry for the priority queue."""

    timestamp: float
    reminder: Reminder


class ReminderService(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self._initialized = False
        # Use a heap as a priority queue for reminders
        self._reminder_queue: list[ScheduledReminder] = []
        self._queue_lock = asyncio.Lock()
        # Store task references to prevent garbage collection
        self._reminder_tasks: set[asyncio.Task[Any]] = set()
        self.reminder_processor.start()

    def _create_reminder_task(self, coro: Coroutine[Any, Any, Any], name: str) -> None:
        """Create a task and store its reference to prevent garbage collection."""
        task = asyncio.create_task(coro, name=name)
        self._reminder_tasks.add(task)
        task.add_done_callback(self._reminder_tasks.discard)

    async def cog_unload(self) -> None:
        """Clean up resources when the cog is unloaded."""
        self.reminder_processor.cancel()
        # Cancel any pending reminder tasks
        for task in self._reminder_tasks.copy():
            task.cancel()
        await asyncio.gather(*self._reminder_tasks, return_exceptions=True)
        self._reminder_tasks.clear()

    @tasks.loop(seconds=5, name="reminder_processor")
    async def reminder_processor(self) -> None:
        """Process reminders from the priority queue."""
        current_time = datetime.datetime.now(datetime.UTC).timestamp()

        async with self._queue_lock:
            # Process all reminders that are due
            while self._reminder_queue and self._reminder_queue[0].timestamp <= current_time:
                scheduled_reminder = heapq.heappop(self._reminder_queue)
                # Schedule the reminder sending as a separate task to avoid blocking the loop
                self._create_reminder_task(
                    self.send_reminder(scheduled_reminder.reminder),
                    f"send_reminder_{scheduled_reminder.reminder.reminder_id}",
                )

    @reminder_processor.before_loop
    async def before_reminder_processor(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

    @reminder_processor.error
    async def on_reminder_processor_error(self, error: BaseException) -> None:
        """Handles errors in the reminder processor loop."""
        logger.error(f"Error in reminder processor loop: {error}")
        if isinstance(error, Exception):
            self.bot.sentry_manager.capture_exception(error)
        else:
            raise error

    async def schedule_reminder(self, reminder: Reminder) -> None:
        """Add a reminder to the priority queue."""
        scheduled = ScheduledReminder(timestamp=reminder.reminder_expires_at.timestamp(), reminder=reminder)

        async with self._queue_lock:
            heapq.heappush(self._reminder_queue, scheduled)

    async def send_reminder(self, reminder: Reminder) -> None:
        user = self.bot.get_user(reminder.reminder_user_id)
        if user is not None:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                user_name=user.name,
                user_display_avatar=user.display_avatar.url,
                title="Reminder",
                description=reminder.reminder_content,
            )

            try:
                await user.send(embed=embed)

            except discord.Forbidden:
                channel = self.bot.get_channel(reminder.reminder_channel_id)

                if isinstance(channel, discord.TextChannel | discord.Thread | discord.VoiceChannel):
                    with contextlib.suppress(discord.Forbidden):
                        await channel.send(
                            content=f"{user.mention} Failed to DM you, sending in channel",
                            embed=embed,
                        )
                        return

                else:
                    logger.error(
                        f"Failed to send reminder {reminder.reminder_id}, DMs closed and channel not found.",
                    )

        else:
            logger.error(
                f"Failed to send reminder {reminder.reminder_id}, user with ID {reminder.reminder_user_id} not found.",
            )

        try:
            await self.db.reminder.delete_reminder_by_id(reminder.reminder_id)
        except Exception as e:
            logger.error(f"Failed to delete reminder: {e}")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self._initialized:
            return

        self._initialized = True

        reminders = await self.db.reminder.get_all_reminders()
        dt_now = datetime.datetime.now(datetime.UTC)

        for reminder in reminders:
            if reminder.reminder_expires_at <= dt_now:
                # Send expired reminders immediately
                self._create_reminder_task(self.send_reminder(reminder), f"expired_reminder_{reminder.reminder_id}")
            else:
                # Schedule future reminders
                await self.schedule_reminder(reminder)

        logger.info(f"Loaded {len(reminders)} existing reminders into queue")


async def setup(bot: Tux) -> None:
    await bot.add_cog(ReminderService(bot))
