import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(name="dev", description="Dev related commands.")
    @commands.has_guild_permissions(administrator=True)
    async def dev(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("dev")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(name="sync_tree", description="Syncs the app command tree.", usage="dev sync_tree <guild>")
    async def sync_tree(self, ctx: commands.Context[commands.Bot], guild: discord.Guild) -> None:
        """
        Syncs the application commands to Discord.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        guild : discord.Guild
            The guild to sync application commands to.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingRequiredArgument
            If a guild is not specified.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return
        # Copy the global tree to the guild
        self.bot.tree.copy_global_to(guild=ctx.guild)
        # Sync the guild tree
        await self.bot.tree.sync(guild=ctx.guild)
        await ctx.reply("Application command tree synced.")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(name="clear_tree", description="Clears the app command tree.", usage="dev clear_tree")
    async def clear_tree(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingPermissions
            If the user does not have the required permissions.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be used in a guild.")
            return

        # Clear the slash command tree for the guild.
        self.bot.tree.clear_commands(guild=ctx.guild)
        # Copy the global slash commands to the guild.
        self.bot.tree.copy_global_to(guild=ctx.guild)
        # Sync the slash command tree for the guild.
        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.reply("Slash command tree cleared.")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(name="load_cog", description="Loads a cog into the bot.", usage="dev load_cog <cog>")
    @app_commands.describe(cog="The name of the cog to load.")
    async def load_cog(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        """
        Loads an cog into the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to load.

        Returns
        -------
        None

        Raises
        ------
        commands.MissingRequiredArgument
            If an cog is not specified.
        commands.ExtensionAlreadyLoaded
            If the specified cog is already loaded.
        commands.ExtensionNotFound
            If the specified cog is not found.
        commands.ExtensionFailed
            If the cog failed to load.
        commands.NoEntryPointError
            If the specified cog does not have a setup function.
        """

        try:
            await self.bot.load_extension(cog)
        except Exception as error:
            await ctx.send(f"Failed to load cog {cog}: {error}")
            logger.error(f"Failed to load cog {cog}: {error}")
        else:
            await ctx.send(f"Cog {cog} loaded.")
            logger.info(f"Cog {cog} loaded.")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(name="unload_cog", description="Unloads a cog from the bot.", usage="dev unload_cog <cog>")
    async def unload_cog(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        """
        Unloads an cog from the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to unload.

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
            await self.bot.unload_extension(cog)
        except Exception as error:
            logger.error(f"Failed to unload cog {cog}: {error}")
            await ctx.send(f"Failed to unload cog {cog}: {error}")
        else:
            logger.info(f"Cog {cog} unloaded.")
            await ctx.send(f"Cog {cog} unloaded.")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(name="reload_cog", description="Reloads a cog into the bot.", usage="dev reload_cog <cog>")
    async def reload_cog(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        """
        Reloads a cog in the bot.

        Parameters
        ----------
        ctx : commands.Context
            The context in which the command is being invoked.
        cog : str
            The name of the cog to reload.

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
            await self.bot.unload_extension(cog)
            await self.bot.load_extension(cog)
        except Exception as error:
            await ctx.send(f"Failed to reload cog {cog}: {error}")
            logger.error(f"Failed to reload cog {cog}: {error}")
        else:
            await ctx.send(f"Cog {cog} reloaded.")
            logger.info(f"Cog {cog} reloaded.")

    @sync_tree.error
    async def sync_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a guild to sync application commands to. {error}")

        else:
            logger.error(f"Error syncing application commands: {error}")

    @reload_cog.error
    async def reload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a cog to reload. {error}")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That cog is not loaded. {error}")
        else:
            await ctx.send(f"Error reloading cog: {error}")
            logger.error(f"Error reloading cog: {error}")

    @unload_cog.error
    async def unload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an extension to unload. {error}")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That cog is not loaded. {error}")
        else:
            logger.error(f"Error unloading cog: {error}")

    @load_cog.error
    async def load_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an cog to load. {error}")
        elif isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.send(f"The specified cog is already loaded. {error}")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.send(f"The specified cog is not found. {error}")
        elif isinstance(error, commands.ExtensionFailed):
            await ctx.send(f"Failed to load cog: {error}")
        elif isinstance(error, commands.NoEntryPointError):
            await ctx.send(f"The specified cog does not have a setup function. {error}")
        else:
            await ctx.send(f"Failed to load cog: {error}")
            logger.error(f"Failed to load cog: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dev(bot))
