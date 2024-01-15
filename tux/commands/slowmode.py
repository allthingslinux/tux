from discord.ext import commands
from tux.command_cog import CommandCog
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class SlowMode(CommandCog):
    @commands.command(name="slowmode", aliases=["sm"])
    async def slowmode(self, ctx: commands.Context, seconds: int):
        """
        Set slow mode for the channel.
        Usage: !slowmode <seconds>
        """
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"Slow mode set to {seconds} seconds!")

        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")


async def setup(bot: commands.Bot):
    await bot.add_cog(SlowMode(bot))
