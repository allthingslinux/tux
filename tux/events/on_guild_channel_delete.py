# on_guild_channel_delete.py
import discord
from discord.ext import commands
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildChannelDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """
        Handles the event when a guild channel gets deleted in a Discord Guild.

        This function is called whenever a guild channel is deleted.

        Note:
            This function requires the `Intents.guilds` to be enabled. You can get the guild from `guild`.

        Args:
            channel (discord.abc.GuildChannel): The guild channel that got deleted.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_channel_delete
        """  # noqa E501

        logger.info(f"{channel} has been deleted in {channel.guild}.")


async def setup(bot):
    await bot.add_cog(OnGuildChannelDelete(bot))
