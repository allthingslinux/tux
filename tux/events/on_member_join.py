# on_member_join.py
import discord
from discord.ext import commands
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """
        Handles the event when a member joins a Discord Guild.

        This function is called when a new member joins a Discord Guild.

        Note:
            This function requires the `Intents.members` to be enabled.

        Args:
            member (discord.Member): The member who has joined the guild.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_member_join
        """  # noqa E501

        # Your on_join logic goes here
        print(f"{member} has joined the server.")


async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))
