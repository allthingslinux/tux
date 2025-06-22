import asyncio
import contextlib
import datetime

import discord
from discord.ext import commands
from loguru import logger

from prisma.models import Reminder
from tux.bot import Tux
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator
from tux.utils.functions import convert_to_seconds, generate_usage


class RemindMe(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.remindme.usage = generate_usage(self.remindme)

    async def send_reminder(self, user_id: int, reminder: Reminder) -> None:
        user = self.bot.get_user(user_id)

        if not user:
            user = await self.bot.fetch_user(user_id)
        
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

    @commands.hybrid_command(
        name="remindme",
        description="Set a reminder for yourself",
    )
    async def remindme(
        self,
        ctx: commands.Context[Tux],
        time: str,
        *,
        reminder: str,
    ) -> None:
        """
        Set a reminder for yourself.

        The time format is `[number][M/w/d/h/m/s]` where:
        - M = months
        - w = weeks
        - d = days
        - h = hours
        - m = minutes
        - s = seconds

        Example: `!remindme 1h30m "Take a break"` will remind you in 1 hour and 30 minutes.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        time : str
            The time to set the reminder for (e.g. 2d, 1h30m).
        reminder : str
            The reminder message.
        """

        seconds = convert_to_seconds(time)

        if seconds == 0:
            await ctx.reply(
                "Invalid time format. Please use the format `[number][M/w/d/h/m/s]`.",
                ephemeral=True,
                delete_after=30,
            )
            return

        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)

        try:
            reminder_obj = await self.db.reminder.insert_reminder(
                reminder_user_id=ctx.author.id,
                reminder_content=reminder,
                reminder_expires_at=expires_at,
                reminder_channel_id=ctx.channel.id if ctx.channel else 0,
                guild_id=ctx.guild.id if ctx.guild else 0,
            )

            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.SUCCESS,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                title="Reminder Set",
                description=f"Reminder set for <t:{int(expires_at.timestamp())}:f>.",
            )

            embed.add_field(
                name="Note",
                value="- If you have DMs closed, we will attempt to send it in this channel instead."
            )

        except Exception as e:
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="There was an error creating the reminder.",
            )

            logger.error(f"Error creating reminder: {e}")

        self.bot.loop.call_later(seconds, asyncio.create_task, self.send_reminder(ctx.author.id, reminder_obj))

        await ctx.reply(embed=embed, ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(RemindMe(bot))
