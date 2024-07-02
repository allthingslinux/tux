from discord.ext import commands
from loguru import logger


class Load(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="load", description="Loads an extension into the bot.", usage="load <extension>")
    async def load(self, ctx: commands.Context[commands.Bot], *, ext: str) -> None:
        """
        Loads an extension into the bot.

        An extension is a python module that contains commands, cogs, or listeners. An extension must have a global function, setup defined as the entry point on what to do when the extension is loaded. This entry point must have a single argument, the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        ext : str
            The name of the extension to load.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingRequiredArgument
            If an extension is not specified.
        commands.ExtensionAlreadyLoaded
            If the specified extension is already loaded.
        commands.ExtensionNotFound
            If the specified extension is not found.
        commands.ExtensionFailed
            If the extension failed to load.
        commands.NoEntryPointError
            If the specified extension does not have a setup function.
        """

        try:
            await self.bot.load_extension(ext)

        except Exception as error:
            await ctx.send(f"Failed to load extension {ext}: {error}")
            logger.error(f"Failed to load extension {ext}: {error}")

        else:
            await ctx.send(f"Extension {ext} loaded.")
            logger.info(f"Extension {ext} loaded.")

    @load.error
    async def load_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an extension to load. {error}")

        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send(f"The specified extension is already loaded. {error}")

        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.send(f"The specified extension is not found. {error}")

        elif isinstance(error, commands.ExtensionFailed):
            await ctx.send(f"Failed to load extension: {error}")

        elif isinstance(error, commands.NoEntryPointError):
            await ctx.send(f"The specified extension does not have a setup function. {error}")

        else:
            await ctx.send(f"Failed to load extension: {error}")
            logger.error(f"Failed to load extension: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Load(bot))
