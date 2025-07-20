import datetime

from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.cogs.services.reminders import ReminderService
from tux.database.controllers import DatabaseController
from tux.ui.embeds import EmbedCreator
from tux.utils.constants import CONST
from tux.utils.functions import convert_to_seconds, generate_usage


class RemindMe(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.remindme.usage = generate_usage(self.remindme)

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

        Example: `$remindme 1h30m take a break` will remind you in 1 hour and 30 minutes.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        time : str
            The time to set the reminder for (e.g. 2d, 1h30m).
        reminder : str
            The reminder message (quotes are not required).
        """

        seconds = convert_to_seconds(time)

        if seconds == 0:
            await ctx.reply(
                "Invalid time format. Please use the format `[number][M/w/d/h/m/s]`.",
                ephemeral=True,
                delete_after=CONST.DEFAULT_DELETE_AFTER,
            )
            return

        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=seconds)
        reminder_service = self.bot.get_cog("ReminderService")

        if not isinstance(reminder_service, ReminderService):
            await ctx.reply("Reminder service not available.", ephemeral=True, delete_after=CONST.DEFAULT_DELETE_AFTER)
            logger.error("ReminderService not found or is not the correct type.")
            return

        try:
            reminder_obj = await self.db.reminder.insert_reminder(
                reminder_user_id=ctx.author.id,
                reminder_content=reminder,
                reminder_expires_at=expires_at,
                reminder_channel_id=ctx.channel.id if ctx.channel else 0,
                guild_id=ctx.guild.id if ctx.guild else 0,
            )

            # Schedule the reminder using our new queue system
            await reminder_service.schedule_reminder(reminder_obj)

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
                value="- If you have DMs closed, we will attempt to send it in this channel instead.\n",
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

        await ctx.reply(embed=embed, ephemeral=True)


async def setup(bot: Tux) -> None:
    await bot.add_cog(RemindMe(bot))
