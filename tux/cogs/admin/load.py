from discord.ext import commands
from loguru import logger


class Load(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="load", description="Loads a cog into the bot.")
    async def load(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        try:
            await self.bot.load_extension(cog)
        except Exception as e:
            logger.error(f"Failed to load cog {cog}: {e}")
            await ctx.send(f"Failed to load cog {cog}: {e}")
        else:
            logger.info(f"Cog {cog} loaded.")
            await ctx.send(f"Cog {cog} loaded.")

    @load.error
    async def load_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to load.")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send("That cog is already loaded.")
        else:
            logger.error(f"Error loading cog: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Load(bot))
