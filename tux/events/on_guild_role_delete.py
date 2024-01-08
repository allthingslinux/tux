import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildRoleDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """
        Handles the event when a role is deleted in a Discord Guild.

        This function is called when a role is deleted in a guild.

        Note:
            This function requires the `Intents.guilds` to be enabled.

        Args:
            role (discord.Role): The role that was deleted.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_role_delete
        """  # noqa E501

        logger.info(f"{role} has been deleted.")


async def setup(bot):
    await bot.add_cog(OnGuildRoleDelete(bot))
