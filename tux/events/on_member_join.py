from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMemberJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """This event is triggered whenever a member joins a guild.

        Args:
            member (discord.Member): Represents a Discord member who joined the Guild.
        """  # noqa E501

        # Your on_join logic goes here
        print(f"{member} has joined the server.")


async def setup(bot):
    await bot.add_cog(OnMemberJoin(bot))
