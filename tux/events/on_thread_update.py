# events/on_thread_update.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnThreadUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_update(self, before: discord.Thread, after: discord.Thread):
        """
        Handles the event when a Thread is updated in a Discord Guild.

        Called whenever a thread is updated. If the thread could not be found in the internal cache this event will not be called. Threads will not be in the cache if they are archived.

        Note:
            This function requires the `Intents.guilds` to be enabled.

        Args:
            before (discord.Thread): The Thread before the update.
            after (discord.Thread): The Thread after the update.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_thread_update
        """  # noqa E501

        logger.info(f"{before} has been updated to {after}.")


async def setup(bot):
    await bot.add_cog(OnThreadUpdate(bot))
