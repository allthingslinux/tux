from collections.abc import Callable, Coroutine

from discord.ext import commands
from discord.ext.commands import (
    BotMissingPermissions,
    CommandNotFound,
    CommandOnCooldown,
    Context,
    MissingPermissions,
    MissingRequiredArgument,
    NotOwner,
)
from utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)

ErrorHandlerFunc = Callable[[Context, Exception], Coroutine[None, None, None]]


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def handle_command_not_found(self, ctx: commands.Context, error):
        """
        Handles the case when an invalid command is used.
        """
        await ctx.send(
            f"I'm sorry, but I couldn't find the command: {ctx.message.content}. Please check your command and try again."
        )
        logger.error(f"CommandNotFound: {error}")

    async def handle_missing_permissions(self, ctx: commands.Context, error):
        """
        Handles the case when a user does not have the necessary permissions
        to use a command.
        """
        await ctx.send(
            "It seems you're missing the necessary permissions to perform this command."
        )
        logger.error(f"MissingPermissions: {error}")

    async def handle_bot_missing_permissions(self, ctx: commands.Context, error):
        """
        Handles the case when the bot does not have the necessary permissions
        to execute a command.
        """
        await ctx.send(
            "I'm sorry, but I don't have enough permissions to perform this command."
        )
        logger.error(f"BotMissingPermissions: {error}")

    async def handle_command_on_cooldown(self, ctx: commands.Context, error):
        """
        Handles the case when a user is on cooldown.
        """
        await ctx.send(
            "You're on cooldown. Please wait a bit before using this command again."
        )
        logger.error(f"Cooldown: {error}")

    async def handle_missing_required_argument(self, ctx: commands.Context, error):
        """
        Handles the case when a user is missing a required argument.
        """
        await ctx.send(
            "You're missing a required argument. Please check your command and try again."
        )
        logger.error(f"MissingRequiredArgument: {error}")

    async def handle_not_owner(self, ctx: commands.Context, error):
        """
        Handles the case when a user is not the owner of the bot.
        """
        await ctx.send("You're not the owner of this bot.")
        logger.error(f"NotOwner: {error}")

    async def handle_other_errors(self, ctx: commands.Context, error):
        """
        Handles all other types of errors.
        """
        logger.exception(f"Unhandled exception in command {ctx.command}: {error}")

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error):
        """Called when an error is raised while invoking a command.

        Args:
            ctx (Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
            error (Exception): The error that was raised.

        Note:
            This function is called when an error is raised while invoking a command. If the error is not
            handled, it will be propagated to the global error handler.

        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.on_command_error
        """
        error_handlers: dict[type[commands.CommandError], ErrorHandlerFunc] = {
            CommandNotFound: self.handle_command_not_found,
            MissingPermissions: self.handle_missing_permissions,
            BotMissingPermissions: self.handle_bot_missing_permissions,
            CommandOnCooldown: self.handle_command_on_cooldown,
            MissingRequiredArgument: self.handle_missing_required_argument,
            NotOwner: self.handle_not_owner,
        }
        handler = error_handlers.get(type(error), self.handle_other_errors)
        await handler(ctx, error)


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
