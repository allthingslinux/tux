from discord.ext import commands

from tux.command_cog import CommandCog
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Load(CommandCog):
    def __init__(self, bot):
        super().__init__(bot)

    @commands.command(name="load")
    async def load(self, ctx: commands.Context, *, cog: str):
        """
        Loads a cog into the bot.

        Args:
            cog (str): The name of the cog to load.

        Example:
            >load commands.load
        """
        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")
            await ctx.send(f"Failed to load cog {cog}: {e}")
        else:
            logger.info(f"Cog {cog} loaded.")
            await ctx.send(f"Cog {cog} loaded.")

    @load.error
    async def load_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to load.")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send("That cog is already loaded.")
        else:
            logger.error(f"Error loading cog: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Load(bot))
