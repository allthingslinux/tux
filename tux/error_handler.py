# error_handler.py
from discord.ext import commands
from utils._tux_logger import TuxLogger

logger = TuxLogger(__name__)


class ErrorHandler:
    @staticmethod
    async def handle_command_not_found(ctx: commands.Context, error):
        await ctx.send("Invalid command used.")

    @staticmethod
    async def handle_missing_permissions(ctx: commands.Context, error):
        await ctx.send("You do not have permission to use this command.")

    @staticmethod
    async def handle_bot_missing_permissions(ctx: commands.Context, error):
        await ctx.send("I do not have permission to execute this command.")

    @staticmethod
    async def handle_other_errors(ctx: commands.Context, error):
        logger.error(error)
