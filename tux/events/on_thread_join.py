# events/on_thread_join.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnThreadJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_join(self, thread: discord.Thread):
        """
        Handles the event when a Thread is joined in a Discord Guild.

        This function is called when a Thread is joined in a Guild.

        Note:
            This function requires the `Intents.guilds` to be enabled.
            You can get the guild from Thread.guild.

        Args:
            thread (discord.Thread): The Thread that was joined.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_thread_join
        """  # noqa E501

        logger.info(f"{thread} has been joined.")


async def setup(bot):
    await bot.add_cog(OnThreadJoin(bot))
