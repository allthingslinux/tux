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

        This only removes the commands locally – in order to sync the commands and remove them in the client, sync() must be called.

        Args:
           ctx (commands.Context): The invocation context sent by the Discord API which contains information
           about the command and from where it was called.

        https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=sync#discord.app_commands.CommandTree.clear_commands
        """

        self.bot.tree.clear_commands(guild=ctx.guild)

        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        logger.info(f"{ctx.author} cleared the slash command tree.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Clear(bot))
