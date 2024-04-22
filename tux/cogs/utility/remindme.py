import contextlib
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from prisma.models import Reminders
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator


# converts something like 1d 2h 3m etc to seconds
def convert_to_seconds(time: str) -> int:
    time = time.lower()
    time_dict = {
        # "s": 1, # disabled because seconds are too short
        "m": 60,
        "h": 3600,
        "d": 86400,
    }

    total_seconds = 0
    current_number = ""
    try:
        for char in time:
            if char.isdigit():
                current_number += char
            else:
                if current_number:
                    total_seconds += int(current_number) * time_dict[char]
                    current_number = ""
    except KeyError:
        # if there is a error parsing the time, return 0 which will be treated as an invalid time
        return 0

    return total_seconds


def get_closest_reminder(reminders: list[Reminders]) -> Reminders | None:
    # check if there are any reminders
    if not reminders:
        return None
    return min(reminders, key=lambda x: x.expires_at)


class RemindMe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController().reminders
        self.bot.loop.create_task(self.update())

    async def execute_reminder(self, reminder: Reminders) -> None:
        user = self.bot.get_user(reminder.user_id)
        if user is not None:
            embed = EmbedCreator.custom_footer_embed(
                ctx=None,
                interaction=None,
                state="SUCCESS",
                user=user,
                latency="N/A",
                content=reminder.content,
                title="Reminder",
            )
            try:
                await user.send(embed=embed)
            except discord.Forbidden:
                # send a message in the channel if the user has DMs closed
                # this is probably a horrible way to do this
                channel: (
                    discord.abc.GuildChannel | discord.Thread | discord.abc.PrivateChannel | None
                ) = self.bot.get_channel(reminder.channel_id)
                if channel is not None and isinstance(
                    channel, discord.TextChannel | discord.Thread | discord.VoiceChannel
                ):
                    with contextlib.suppress(discord.Forbidden):
                        await channel.send(
                            content=f"{user.mention} Failed to DM you, sending in channel",
                            embed=embed,
                        )
        await self.db_controller.delete_reminder(reminder.id)
        # run update again to check if there are any more reminders
        await self.update()

    async def end_timer(self, reminder: Reminders) -> None:
        await discord.utils.sleep_until(reminder.expires_at)
        await self.execute_reminder(reminder)

    async def update(self) -> None:
        # get the closest reminder
        reminders = await self.db_controller.get_all_reminders()
        closest_reminder = get_closest_reminder(reminders)

        if closest_reminder is None:
            # no reminders, return
            return

        # check if its already expired
        if closest_reminder.expires_at < datetime.datetime.now(datetime.UTC):
            await self.execute_reminder(closest_reminder)
            return

        # create a task to wait until the reminder expires
        self.bot.loop.create_task(self.end_timer(closest_reminder))

    @app_commands.command(
        name="remindme", description="Reminds you after a certain amount of time."
    )
    async def remindme(self, interaction: discord.Interaction, time: str, *, reminder: str) -> None:
        seconds = convert_to_seconds(time)
        if seconds == 0:
            await interaction.response.send_message(
                "Invalid time format. Please use a format like `1d`, `2h`, `3m`, etc. (only days, hours, and minutes are supported)"
            )
            return

        seconds = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)

        await self.db_controller.create_reminder(
            user_id=interaction.user.id,
            reminder_content=reminder,
            expires_at=seconds,
            channel_id=interaction.channel_id or 0,
            guild_id=interaction.guild_id or 0,
        )

        embed = EmbedCreator.create_default_embed(
            title="Reminder Set",
            description=f"Reminder set for <t:{int(seconds.timestamp())}:f>.",
            interaction=interaction,
        )

        EmbedCreator.add_field(
            embed,
            name="Note",
            value="If you have DMs closed, the reminder may not reach you. We will attempt to send it in this channel instead, however it is not guaranteed.",
        )

        await interaction.response.send_message(embed=embed)

        # run update again to check if this reminder is the closest
        await self.update()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemindMe(bot))
