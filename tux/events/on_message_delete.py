import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMessageDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """
        Handles the event when a message gets deleted from a Discord Guild.

        This function is called when a message gets deleted. If the message is not found in the internal
        message cache, then this event will not be called. Messages might not be in cache if the message
        is too old or the client is participating in high traffic guilds.

        If this occurs increase the `max_messages` parameter or use the `on_raw_message_delete()` event instead.

        Note:
            This function requires the `Intents.messages` to be enabled.

        Args:
            message (discord.Message): The deleted message.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_message_delete
        """  # noqa E501

        logger.info(f"Message deleted: {message.content}")


async def setup(bot):
    await bot.add_cog(OnMessageDelete(bot))
