import discord
from discord.ext import commands
from loguru import logger


class Dev(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_group(name="dev", description="Dev related commands.", aliases=["d"])
    @commands.has_guild_permissions(administrator=True)
    async def dev(self, ctx: commands.Context[commands.Bot]) -> None:
        if ctx.invoked_subcommand is None:
            await ctx.send_help("dev")

    @commands.has_permissions(administrator=True)
    @dev.command(name="sync_tree", usage="$dev sync_tree <guild>", aliases=["sync", "st"])
    async def sync_tree(self, ctx: commands.Context[commands.Bot], guild: discord.Guild) -> None:
        """
        Syncs the app command tree.

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

    @sync_tree.error
    async def sync_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a guild to sync application commands to. {error}")
        else:
            logger.error(f"Error syncing application commands: {error}")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(
        name="clear_tree",
        usage="$dev clear_tree",
        aliases=["clear", "ct"],
    )
    async def clear_tree(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Clears the app command tree.

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
    @dev.command(
        name="load_cog",
        usage="dev load_cog <cog>",
        aliases=["load", "lc"],
    )
    async def load_cog(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        """
        Loads a cog into the bot.

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

    @commands.has_guild_permissions(administrator=True)
    @dev.command(
        name="unload_cog",
        usage="dev unload_cog <cog>",
        aliases=["unload", "uc"],
    )
    async def unload_cog(self, ctx: commands.Context[commands.Bot], *, cog: str) -> None:
        """
        Unloads a cog from the bot.

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

    @unload_cog.error
    async def unload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify an extension to unload. {error}")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That cog is not loaded. {error}")
        else:
            logger.error(f"Error unloading cog: {error}")

    @commands.has_guild_permissions(administrator=True)
    @dev.command(
        name="reload_cog",
        usage="dev reload_cog <cog>",
        aliases=["reload", "rc"],
    )
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

    @reload_cog.error
    async def reload_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a cog to reload. {error}")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.send(f"That cog is not loaded. {error}")
        else:
            await ctx.send(f"Error reloading cog: {error}")
            logger.error(f"Error reloading cog: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dev(bot))
