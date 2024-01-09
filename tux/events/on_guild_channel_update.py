# on_guild_channel_update.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildChannelUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ):
        """
        Called whenever a guild channel is updated. e.g. changed name, topic, permissions.

        This function is called whenever a guild channel is updated.

        Note:
            This function requires the `Intents.guilds` to be enabled. You can get the guild from `guild`.

        Args:
            before (discord.abc.GuildChannel): The updated channel’s old info.
            after (discord.abc.GuildChannel): The updated channel’s updated info.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_channel_update
        """  # noqa E501

        logger.info(f"{before} has been updated to {after}.")

        # TODO:

        # Compare the before and after channel objects and
        # do something with the differences.


async def setup(bot):
    await bot.add_cog(OnGuildChannelUpdate(bot))
