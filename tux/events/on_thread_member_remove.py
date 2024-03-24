# events/on_thread_member_join.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnThreadMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_member_remove(self, member: discord.ThreadMember):
        """
        Handles the event when a Member leaves a Thread in a Discord Guild.

        Note:
            This function requires the `Intents.guilds` to be enabled.
            You can get the thread a member belongs in by accessing ThreadMember.thread.

        Args:
            member (discord.ThreadMember): The Member that left the Thread.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_thread_member_remove
        """  # noqa E501

        thread = member.thread

        logger.info(f"{member} has left {thread}.")


async def setup(bot):
    await bot.add_cog(OnThreadMemberRemove(bot))
