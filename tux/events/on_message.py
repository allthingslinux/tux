import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """This event is triggered whenever a message is sent in a channel.

        Args:
            message (discord.Message): Represents a Discord message.
        """  # noqa E501
        if message.author == self.bot.user:
            return

        if message.content.startswith("!hello"):
            await message.channel.send("Hello!")


async def setup(bot):
    await bot.add_cog(OnMessage(bot))
