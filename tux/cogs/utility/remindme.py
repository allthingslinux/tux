import contextlib
import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks
from loguru import logger

from prisma.models import Reminder
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator
from tux.utils.functions import convert_to_seconds


class RemindMe(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController().reminder
        self.check_reminders.start()

    @tasks.loop(seconds=120)
    async def check_reminders(self):
        reminders = await self.db.get_unsent_reminders()

        for reminder in reminders:
            await self.send_reminder(reminder)
            await self.db.update_reminder_status(reminder.reminder_id, sent=True)
            logger.debug(f'Status of reminder {reminder.reminder_id} updated to "sent".')

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
                        f"Failed to send reminder to {user.id}, DMs closed and channel not found.",
                    )

        else:
            logger.error(f"Failed to send reminder to {reminder.reminder_user_id}, user not found.")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @app_commands.command(
        name="remindme",
        description="Reminds you after a certain amount of time.",
    )
    async def remindme(self, interaction: discord.Interaction, time: str, *, reminder: str) -> None:
        seconds = convert_to_seconds(time)

        if seconds == 0:
            await interaction.response.send_message(
                "Invalid time format. Please use the format `[number][M/w/d/h/m/s]`.",
                ephemeral=True,
                delete_after=30,
            )
            return

        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)

        try:
            await self.db.insert_reminder(
                reminder_user_id=interaction.user.id,
                reminder_content=reminder,
                reminder_expires_at=expires_at,
                reminder_channel_id=interaction.channel_id or 0,
                guild_id=interaction.guild_id or 0,
            )

            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.SUCCESS,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                title="Reminder Set",
                description=f"Reminder set for <t:{int(expires_at.timestamp())}:f>.",
            )

            embed.add_field(
                name="Note",
                value="- If you have DMs closed, we will attempt to send it in this channel instead.\n"
                "- The reminder may be delayed by up to 120 seconds due to the way Tux works.",
            )

        except Exception as e:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=interaction.user.name,
                user_display_avatar=interaction.user.display_avatar.url,
                description="There was an error creating the reminder.",
            )

            logger.error(f"Error creating reminder: {e}")

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(RemindMe(bot))
