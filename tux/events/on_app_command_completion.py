# events/on_app_command_completion.py

import discord
from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnAppCommandCompletion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        """
        Handles the event when an application command is completed successfully.

        This method is called when a discord.app_commands.Command
        or discord.app_commands.ContextMenu has completed execution
        successfully without any error.

        Args:
            interaction (discord.Interaction): The Interaction instance linked with the application command.
            command (Union[app_commands.Command, app_commands.ContextMenu]): The command that completed execution successfully.

        Note:
        This method logs the details of the application command's use,
        which includes the user who invoked the command, the command name,
        and the channel in which it was used.

        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.on_app_command_completion
        """

        logger.info(
            f"'{command.name}' command was used by {interaction.user} in {interaction.channel}."
        )


async def setup(bot: commands.Bot):
    """
    Set up function for loading the 'OnAppCommandCompletion' cog.

    Adds an instance of 'OnAppCommandCompletion' to the bot's cogs.
    """
    await bot.add_cog(OnAppCommandCompletion(bot))
