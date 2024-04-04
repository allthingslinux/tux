from discord.ext import commands
from loguru import logger


class Unload(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="unload", description="Unloads a cog from the bot.")
    async def unload(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        try:
            await self.bot.unload_extension(cog)
        except Exception as e:
            logger.error(f"Failed to unload cog {cog}: {e}")
            await ctx.send(f"Failed to unload cog {cog}: {e}")
        else:
            logger.info(f"Cog {cog} unloaded.")
            await ctx.send(f"Cog {cog} unloaded.")

    @unload.error
    async def unload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a cog to unload.")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send("That cog is not loaded.")
        else:
            logger.error(f"Error unloading cog: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unload(bot))
