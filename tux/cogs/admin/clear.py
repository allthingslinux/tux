from discord.ext import commands
from loguru import logger


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="clear", description="Clears the slash command tree.", usage="clear")
    async def clear(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Clears the slash command tree for the guild.

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

        await ctx.send("Slash command tree cleared.")

        logger.info(f"{ctx.author} cleared the slash command tree.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
