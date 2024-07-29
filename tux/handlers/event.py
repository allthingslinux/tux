import discord
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.utils.functions import is_harmful, strip_formatting


class EventHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        await self.db.guild.insert_guild_by_id(guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild) -> None:
        await self.db.guild.delete_guild_by_id(guild.id)

    async def handle_harmful_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        stripped_content = strip_formatting(message.content)

        if is_harmful(stripped_content):
            await message.reply(
                "Warning: This command is potentially harmful. Please avoid running it unless you're fully aware of it's operation. If this was a mistake, disregard this message.",
            )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        await self.handle_harmful_message(after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.handle_harmful_message(message)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventHandler(bot))
