import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux

# Configuration

CHANNEL_ID = 1172343581495795752  # channel to monitor
EXTRA_BANNED_EMOJIS = []  # should be unicode emoji list, e.g. ["☹️", "😀", "🪊"], blocks all unicode country flags and any emoji that has "flag" in the name by default

# -- DO NOT CHANGE ANYTHING BELOW THIS LINE --


class FlagRemover(BaseCog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        user = self.bot.get_user(payload.user_id)
        if user is None or user.bot:
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
        if channel is None or channel.id != CHANNEL_ID or not isinstance(channel, discord.TextChannel):
            return

        message = await channel.fetch_message(payload.message_id)

        emoji = payload.emoji
        if (
            any(0x1F1E3 <= ord(char) <= 0x1F1FF for char in emoji.name)
            or "flag" in emoji.name.lower()
            or emoji.name in EXTRA_BANNED_EMOJIS
        ):
            await message.remove_reaction(emoji, member)
            return


async def setup(bot: Tux) -> None:
    await bot.add_cog(FlagRemover(bot))
