from discord.ext import commands
from loguru import logger


class Reload(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="reload", description="Reloads a cog in the bot.")
    async def reload(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
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
    async def reload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to reload.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("That cog is not loaded.")
        else:
            logger.error(f"Error reloading cog: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reload(bot))
