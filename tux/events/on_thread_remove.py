# events/on_thread_remove.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnThreadRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_remove(self, thread: discord.Thread):
        """
        Handles the event when a Thread is removed in a Discord Guild.

        Called whenever a thread is removed. This is different from a thread being deleted.

        Due to technical limitations, this event might not be called as soon as one expects. Since the library tracks thread membership locally, the API only sends updated thread membership status upon being synced by joining a thread.

        Note:
            This function requires the `Intents.guilds` to be enabled.
            You can get the guild from Thread.guild.

        Args:
            thread (discord.Thread): The Thread that was removed.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_thread_remove
        """  # noqa E501

        logger.info(f"{thread} has been removed.")


async def setup(bot):
    await bot.add_cog(OnThreadRemove(bot))
