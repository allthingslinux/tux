# on_guild_role_update.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnGuildRoleUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """
        Handles the event when a role is changed in a Discord Guild.

        This function is called when a role is changed in a guild.

        Note:
            This function requires the `Intents.guilds` to be enabled.

        Args:
            before (discord.Role): TThe updated role’s old info.
            after (discord.Role): The updated role’s updated info.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_guild_role_update
        """  # noqa E50

        logger.info(f"{before} has been updated to {after}.")


async def setup(bot):
    await bot.add_cog(OnGuildRoleUpdate(bot))
