# commands/unload.py

from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Unload(CommandCog):
    @commands.hybrid_command(name="unload", description="Unloads a cog from the bot.")
    async def unload(self, ctx: commands.Context, *, cog: str) -> None:
        """
        Unloads a cog from the bot.

        Args:
            cog (str): The name of the cog to unload.

        Example:
            >unload commands.unload
        """

        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            logger.error(f"Failed to unload cog {cog}: {e}")
            await ctx.send(f"Failed to unload cog {cog}: {e}")
        else:
            logger.info(f"Cog {cog} unloaded.")
            await ctx.send(f"Cog {cog} unloaded.")

    @unload.error
    async def unload_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to unload.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("That cog is not loaded.")
        else:
            logger.error(f"Error unloading cog: {error}")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Unload(bot))
