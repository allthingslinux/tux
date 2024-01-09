# on_guild_channel_create.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildChannelCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        """
        Handles the event when a guild channel gets created in a Discord Guild.

        This function is called whenever a guild channel is created.

        Note:
            This function requires the `Intents.guilds` to be enabled. You can get the guild from `guild`.

        Args:
            channel (discord.abc.GuildChannel): The guild channel that got created.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_channel_create
        """  # noqa E501

        logger.info(f"{channel} has been created in {channel.guild}.")


async def setup(bot):
    await bot.add_cog(OnGuildChannelCreate(bot))
