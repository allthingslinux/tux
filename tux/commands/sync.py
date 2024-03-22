from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Sync(CommandCog):
    @commands.hybrid_command(
        name="sync", description="Syncs the application commands to Discord."
    )
    async def sync(self, ctx: commands.Context, guild=None) -> None:
        """
        Syncs the application commands to Discord.
        """

        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)

        await self.bot.tree.sync(guild=ctx.guild)

        logger.info(f"{ctx.author} synced the application command tree.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Sync(bot))
