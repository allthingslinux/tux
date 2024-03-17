# on_member_join.py
import discord
import discord.utils
from discord.ext import commands

from tux.constants import C
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnVoiceStateUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        # Your on_join logic goes here
        print(f"Voice state update: {member.name} {before.channel} -> {after.channel}")
        print(f"Constants: {C.TEMPVC_CATEGORY} {C.TEMPVC_CHANNEL}")

        if (
            before.channel is None
            and after.channel
            and after.channel.id == int(C.TEMPVC_CHANNEL or "0")
        ):
            new_channel = await after.channel.clone(name=f"[TEMP] - {member.name}")
            await member.move_to(new_channel)
            return

        if before.channel is not None:
            category = discord.utils.get(
                before.channel.guild.categories, id=int(C.TEMPVC_CATEGORY or "0") or 0
            )

            if category is None:
                return
            if before.channel.category_id != category.id:
                return
            if before.channel == after.channel:  # User did not disconnect
                return
            if not before.channel.name.startswith("[TEMP]"):
                return
            # get the number of members in the channel
            if len(before.channel.members) == 0:
                await before.channel.delete()
                return


async def setup(bot):
    await bot.add_cog(OnVoiceStateUpdate(bot))
