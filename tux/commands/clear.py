# commands/clear.py

from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Clear(CommandCog):
    @commands.hybrid_command(name="clear", description="Clears the slash command tree.")
    async def clear(self, ctx: commands.Context) -> None:
        """
        Clears the slash command tree.
        """

        self.bot.tree.clear_commands(guild=ctx.guild)

        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        logger.info(f"{ctx.author} cleared the slash command tree.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Clear(bot))
