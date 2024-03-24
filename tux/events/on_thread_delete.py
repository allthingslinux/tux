# events/on_thread_delete.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnThreadDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_delete(self, thread: discord.Thread):
        """
        Called whenever a thread is deleted. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.

        If you need this information use on_raw_thread_delete() instead.

        Note:
            This function requires the `Intents.guilds` to be enabled.
            You can get the guild from Thread.guild.

        Args:
            thread (discord.Thread): The Thread that was deleted.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_thread_delete
        """  # noqa E501

        logger.info(f"{thread} has been deleted.")


async def setup(bot):
    await bot.add_cog(OnThreadDelete(bot))
