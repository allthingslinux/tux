from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Reload(CommandCog):
    @commands.hybrid_command(name="reload", description="Reloads a cog in the bot.")
    async def reload(self, ctx: commands.Context, *, cog: str) -> None:
        """
        Reloads a cog in the bot.

        Args:
            cog (str): The name of the cog to reload.

        Example:
            >reload commands.reload
        """
        if cog == "config":
            self.bot.permissions.reload_ini_file("config/settings.ini")
            return

        try:
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
        except Exception as e:
            logger.error(f"Failed to reload cog {cog}: {e}")
            await ctx.send(f"Failed to reload cog {cog}: {e}")
        else:
            logger.info(f"Cog {cog} reloaded.")
            await ctx.send(f"Cog {cog} reloaded.")

    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to reload.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("That cog is not loaded.")
        else:
            logger.error(f"Error reloading cog: {error}")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Reload(bot))
