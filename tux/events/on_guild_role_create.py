# on_guild_role_create.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildRoleCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """
        Handles the event when a role is created in a Discord Guild.

        This function is called when a role is created in a guild.

        Note:
            This function requires the `Intents.guilds` to be enabled.

        Args:
            role (discord.Role): The role that was created.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_role_create
        """  # noqa E501

        logger.info(f"{role} has been created.")


async def setup(bot):
    await bot.add_cog(OnGuildRoleCreate(bot))
