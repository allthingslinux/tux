import logging
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name='ping')
    async def ping(self, ctx: commands.Context):
        """
        Pong!
        """
        await ctx.send('Pong!')


async def setup(bot, debug=False):
    if debug: logger.setLevel(logging.DEBUG)
    await bot.add_cog(Ping(bot))