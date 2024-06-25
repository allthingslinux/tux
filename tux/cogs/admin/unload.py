from discord.ext import commands
from loguru import logger


class Unload(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="unload", description="Unloads an extension from the bot.", usage="unload <extension>")
    async def unload(self, ctx: commands.Context[commands.Bot], *, ext: str) -> None:
        """
        Unloads an extension from the bot.

        An extension is a Python module that generally contains commands, cogs, or listeners. For an extension to be unloaded properly, it should have a previously loaded state established by a 'setup' function defined at its entry point. This 'setup' function should accept the bot instance as its sole argument.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        ext : str
            The name of the extension to unload.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingRequiredArgument
            If an extension name is not specified.
        commands.ExtensionNotLoaded
            If the specified extension is not loaded or doesn't exist.
        """

        try:
            await self.bot.unload_extension(ext)

        except Exception as error:
            logger.error(f"Failed to unload extension {ext}: {error}")
            await ctx.send(f"Failed to unload extension {ext}: {error}")

        else:
            logger.info(f"Extension {ext} unloaded.")
            await ctx.send(f"Extension {ext} unloaded.")

    @unload.error
    async def unload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an extension to unload. {error}")

        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That extension is not loaded. {error}")

        else:
            logger.error(f"Error unloading extension: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unload(bot))
