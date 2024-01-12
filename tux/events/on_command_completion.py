# events/on_command_completion.py

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnCommandCompletion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """
        Handles the event when a command is completed successfully.

        This function is triggered when a command has been executed
        successfully without any error.

        Args:
            ctx (commands.Context): The Context instance of the command.

        Note:
        This function adds a checkmark reaction to the message indicating
        successful execution and logs the details of the command
        execution, including the author, the command, and the channel.

        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.on_command_completion
        """

        # Add a reaction to the command message indicating its successful completion.
        await ctx.message.add_reaction("✅")

        # Log the successful command execution details.
        logger.info(
            f"'{ctx.command}' command was used by {ctx.author} in {ctx.channel}."
        )


async def setup(bot: commands.Bot):
    """
    Set up function for loading the 'OnCommandCompletion' cog.

    Adds an instance of 'OnCommandCompletion' to the bot's cogs.
    """
    await bot.add_cog(OnCommandCompletion(bot))
