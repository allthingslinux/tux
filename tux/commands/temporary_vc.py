import discord
import discord.utils
from discord.ext import commands

from tux.command_cog import CommandCog
from tux.constants import C
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class TempVC(CommandCog):
    @commands.Cog.listener()
    async def on_voice_state_update(
        self, _: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        """
        Deletes a temporary VC. This should not be called explicitly!
        """
        if before.channel is None:  # Joining VC
            return
        category = discord.utils.get(
            before.channel.guild.categories, id=int(C.TEMPVC_CATEGORY or "0") or 0
        )
        if category is None:  # Safety check
            return
        if before.channel.category_id != category.id:  # Event happened in irrelevant VC
            return
        if before.channel == after.channel:  # User did not disconnect
            return
        await before.channel.delete()

    @commands.guild_only()
    @commands.hybrid_command(name="createvc")
    async def createvc(self, ctx: commands.Context, name: str):
        """
        Creates a VC that automatically deletes itself when all members leave.
        """

        async def err(reason):
            await ctx.reply(reason)

        guild = ctx.guild
        if guild is None:  # Safety check
            return await err("Invalid guild. Stop DMing this bot.")
        category = discord.utils.get(
            guild.categories, id=int(C.TEMPVC_CATEGORY or "0") or 0
        )
        if category is None:  # Invalid TEMPVC_CATEGORY
            return await err("Invalid category. This is the bot owner's fault.")

        vcmax = int(C.TEMPVC_MAX or "0") or 0

        if len(category.channels) >= vcmax:
            return await err(
                f"The maximum number of VCs ({vcmax}) have already been made."
            )
        await category.create_voice_channel(name)

        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(TempVC(bot))
