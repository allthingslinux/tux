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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        user = self.bot.get_user(payload.user_id)
        if user is None:
            return
        if user.bot:
            return

        if payload.guild_id is None:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        channel = guild.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.type != discord.ChannelType.text:
            return

        message = await channel.fetch_message(payload.message_id)
        if not message:
            return

        emoji = payload.emoji
        if any(0x1F1E6 <= ord(char) <= 0x1F1FF for char in emoji.name):
            await message.remove_reaction(emoji, member)
            return
        if "flag" in emoji.name.lower():
            await message.remove_reaction(emoji, member)
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventHandler(bot))
