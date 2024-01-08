import discord
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnMessageEdit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """
        Handles the event when a Message receives an update.

        This function is called when a message is edited. If the message is not found
        in the internal message cache, these events will not be called. This usually
        happens if the message is too old or the client is participating in high traffic guilds.
        In such cases, consider increasing the `max_messages` parameter or use the
        `on_raw_message_edit()` event instead.

        This function is triggered by the following non-exhaustive cases:
            - A message has been pinned or unpinned.
            - The message content has been changed.
            - The message has received an embed.
            - The message’s embeds were suppressed or unsuppressed.
            - A call message has received an update to its participants or ending time.

        Note:
            This function requires the `Intents.messages` to be enabled.

        Args:
            before (discord.Message): The previous version of the message.
            after (discord.Message): The current version of the message after the update.

        https://discordpy.readthedocs.io/en/stable/api.html#discord.on_message_edit
        """  # noqa E501

        logger.info(f"Message before: {before.content}")
        logger.info(f"Message after: {after.content}")


async def setup(bot):
    await bot.add_cog(OnMessageEdit(bot))
