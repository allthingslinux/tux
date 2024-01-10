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
        # ctx: commands.Context, <-- is this needed?
        interaction: discord.Interaction,
        command: discord.app_commands.Command | discord.app_commands.ContextMenu,
    ):
        """
        Handles the event when an application command is completed successfully.

        Called when a app_commands.Command or app_commands.ContextMenu has successfully completed without error.

        Args:
            interaction (discord.Interaction): The Interaction that was used.
            command (Union[app_commands.Command, app_commands.ContextMenu]): The command that completed successfully

        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.discord.ext.commands.on_app_command_completion
        """  # noqa E501
        logger.info(f"{interaction.user} used {command.name} in {interaction.channel}.")


async def setup(bot):
    await bot.add_cog(OnAppCommandCompletion(bot))
