# commands/reload.py

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="reload")
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, *, cog: str):
        """
        Reloads a cog in the bot.

        Args:
            cog (str): The name of the cog to reload.

        Example:
            >reload commands.reload
        """

        try:
            await self.bot.reload_extension(cog)
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Reload(bot))
