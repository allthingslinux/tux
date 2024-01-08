import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberRemove(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Handles the event when a Member leaves a Discord Guild.

        This function is called when a member leaves a Guild. If the Guild or
        member could not be found in the internal cache this event will not be
        fired, consider using on_raw_member_remove() in such cases.

        Note:
            This function requires the `Intents.members` to be enabled.

        Args:
            member (discord.Member): The member who left the Guild.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_remove
        """  # noqa E501

        print(f"{member} has left the server.")


async def setup(bot):
    await bot.add_cog(OnMemberRemove(bot))
