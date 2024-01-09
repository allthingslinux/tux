# on_member_unban.py
import discord
from discord.ext import commands
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberUnban(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """
        Handles the event when a user gets unbanned from a Discord Guild.

        This function is called when a user gets unbanned from a guild.

        Note:
            This function requires the `Intents.moderation` to be enabled.

        Args:
            guild (discord.Guild): The guild the user got unbanned from.
            user (discord.User): The user that got unbanned.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_unban
        """  # noqa E501

        print(f"{user} has been unbanned from the server.")


async def setup(bot):
    await bot.add_cog(OnMemberUnban(bot))
