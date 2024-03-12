# commands/sync.py

from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Sync(CommandCog):
    @commands.hybrid_command(
        name="sync", description="Syncs the application commands to Discord."
    )
    async def sync(self, ctx: commands.Context, guild=None) -> None:
        """
        Syncs the application commands to Discord.

        This function is a coroutine.

        This also runs the translator to get the translated strings necessary for feeding back into Discord.
        This must be called for the application commands to show up.

        Args:
            guild (Optional[Snowflake]): The guild to sync the commands to. If None then it syncs all global commands instead.

        Raises:
            HTTPException: Syncing the commands failed.
            CommandSyncFailure: Syncing the commands failed due to a user related error, typically because the command has invalid data. This is equivalent to an HTTP status code of 400.
            Forbidden: The client does not have the applications.commands scope in the guild.
            MissingApplicationID: The client does not have an application ID.
            TranslationError: An error occurred while translating the commands.

        Returns:
            The application’s commands that got synced.
        Return type:
            List[AppCommand]

        Note:
            This function requires the 'Intents.commands' to be enabled.

        https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=sync#discord.app_commands.CommandTree.sync
        """  # noqa E501

        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)
        logger.info(f"{ctx.author} synced the application command tree.")


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Sync(bot))
