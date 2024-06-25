from discord.ext import commands
from loguru import logger


class Reload(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="reload", description="Reloads an extension into the bot.", usage="reload <extension>")
    async def reload(self, ctx: commands.Context[commands.Bot], *, ext: str) -> None:
        """
        Reloads an extension in the bot.

        An extension is a python module that contains commands, cogs, or listeners. An extension must have a global function, setup defined as the entry point on what to do when the extension is loaded. This entry point must have a single argument, the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        ext : str
            The name of the extension to reload.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingRequiredArgument
            If an extension is not specified.
        commands.ExtensionNotLoaded
            If the specified extension is not loaded or doesn't exist.
        """

        try:
            # Unload and load the cog to "reload" it
            await self.bot.unload_extension(ext)
            await self.bot.load_extension(ext)

        except Exception as error:
            await ctx.send(f"Failed to reload extension {ext}: {error}")
            logger.error(f"Failed to reload extension {ext}: {error}")

        else:
            await ctx.send(f"Extension {ext} reloaded.")
            logger.info(f"Extension {ext} reloaded.")

    @reload.error
    async def reload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an extension to reload. {error}")

        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That extension is not loaded. {error}")

        else:
            await ctx.send(f"Error reloading extension: {error}")
            logger.error(f"Error reloading extension: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Reload(bot))
