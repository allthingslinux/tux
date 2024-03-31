import discord
from discord.ext import commands
from loguru import logger


class MessageEventsCog(commands.Cog, name="Message Events Handler"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]) -> None:
        logger.trace(f"Messages deleted: {messages}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        logger.trace(f"Message deleted: {message}")

        # if sender is a bot, ignore, some bots delete their own messages
        if message.author.bot:
            return

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        logger.trace(f"Message edited: {before} -> {after}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        logger.trace(f"Message received: {message}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MessageEventsCog(bot))
