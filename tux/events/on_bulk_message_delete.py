# on_bulk_message_delete.py
import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnBulkMessageDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]):
        """
        Handles the event when messages are bulk deleted from a Discord Guild.

        This function is called when multiple messages get deleted. If none of the messages deleted are found
        in the internal message cache, then this event will not be called. If individual messages were not found
        in the internal message cache, this event will still be called, but the messages not found will not be
        included in the messages list. Messages might not be in cache if the message is too old or the client
        is participating in high traffic guilds.

        If this occurs increase the `max_messages` parameter or use the `on_raw_bulk_message_delete()` event instead.

        Note:
            This function requires the `Intents.messages` to be enabled.

        Args:
            messages (list[discord.Message]): The messages that have been deleted.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_bulk_message_delete
        """  # noqa E501

        logger.info(f"Messages deleted: {messages}")


async def setup(bot):
    await bot.add_cog(OnBulkMessageDelete(bot))
