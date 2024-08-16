import discord
from discord.ext import commands

from tux.database.controllers import DatabaseController
from tux.utils.functions import get_harmful_command_type, is_harmful, strip_formatting


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
            bad_command_type: str = get_harmful_command_type(stripped_content)
            if bad_command_type == "rm":
                await message.reply(
                    "⚠️ **This command is likely harmful.**\n-# By running it, **all directory contents will be deleted. There is no undo.** Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it. [Learn more](<https://itsfoss.com/sudo-rm-rf/>)",
                )
            else:
                await message.reply(
                    f"⚠️ **This command may be harmful.** Please ensure you understand its effects before proceeding. If you received this message in error, please disregard it.",
                )
                await message.reply(
                    "⚠️ **This command is likely harmful.**\n-# By running it, **all directory contents will be deleted. There is no undo.** Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it. [Learn more](<https://itsfoss.com/sudo-rm-rf/>)",
                )
            elif bad_command_type == "dd":
                await message.reply(
                    "⚠️ **This command is likely harmful.**\n-# By running it, **all data on the specified disk will be erased. There is no undo.** Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.",
                )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if not is_harmful(before.content) and is_harmful(after.content):
            await self.handle_harmful_message(after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.handle_harmful_message(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        flag_list = ["🏳️‍🌈", "🏳️‍⚧️"]

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

        channel = self.bot.get_channel(payload.channel_id)
        if channel is None:
            return
        if channel.id != 1172343581495795752:
            return
        if not isinstance(channel, discord.TextChannel):
            return

        message = await channel.fetch_message(payload.message_id)

        emoji = payload.emoji
        if any(0x1F1E3 <= ord(char) <= 0x1F1FF for char in emoji.name):
            await message.remove_reaction(emoji, member)
            return
        if "flag" in emoji.name.lower():
            await message.remove_reaction(emoji, member)
            return
        if emoji.name in flag_list:
            await message.remove_reaction(emoji, member)
            return


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EventHandler(bot))
