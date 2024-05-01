import discord
from discord.ext import commands
from loguru import logger


class Sync(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(
        name="sync", description="Syncs the application commands to Discord.", usage="sync <guild>"
    )
    async def sync(self, ctx: commands.Context[commands.Bot], guild: discord.Guild) -> None:
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

        logger.info(f"{ctx.author} synced the application command tree.")

    @sync.error
    async def sync_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Please specify a guild to sync application commands to. {error}")

        else:
            logger.error(f"Error syncing application commands: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sync(bot))
