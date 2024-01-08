from discord.ext import commands
from utils.tux_logger import TuxLogger

# Initialize logger
logger = TuxLogger(__name__)


class ErrorHandler:
    """
    ErrorHandler class to handle different types of errors in discord commands.
    """

    @staticmethod
    async def handle_command_not_found(ctx: commands.Context, error):
        """
        Handles the case when an invalid command is used.

        Parameters:
        ctx (commands.Context): The context in which a command is called.
        error (Exception): The error raised by the invalid command.
        """
        await ctx.send("Invalid command used.")

    @staticmethod
    async def handle_missing_permissions(ctx: commands.Context, error):
        """
        Handles the case when a user does not have the necessary permissions
        to use a command.

        Parameters:
        ctx (commands.Context): The context in which a command is called.
        error (Exception): The error raised due to missing permissions.
        """
        await ctx.send("You do not have permission to use this command.")

    @staticmethod
    async def handle_bot_missing_permissions(ctx: commands.Context, error):
        """
        Handles the case when the bot does not have the necessary permissions
        to execute a command.

        Parameters:
        ctx (commands.Context): The context in which a command is called.
        error (Exception): The error raised due to bot's missing permissions.
        """
        await ctx.send("I do not have permission to execute this command.")

    @staticmethod
    async def handle_other_errors(ctx: commands.Context, error):
        """
        Handles all other types of errors.

        Parameters:
        ctx (commands.Context): The context in which a command is called.
        error (Exception): The error raised.
        """
        logger.error(error)
