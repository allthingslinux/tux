# from discord.ext import commands

from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.content.startswith("!hello"):
            await message.channel.send("Hello!")


async def setup(bot):
    # cog = OnMessage(bot)
    # logger.info(f"Setting up {cog.__class__.__name__}...")
    await bot.add_cog(OnMessage(bot))
