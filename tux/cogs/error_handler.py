import traceback

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

# Custom error handling mappings and messages.
error_map = {
    # app_commands
    app_commands.AppCommandError: "An error occurred: {error}",
    app_commands.CommandInvokeError: "A command invoke error occurred: {error}",
    app_commands.TransformerError: "A transformer error occurred: {error}",
    app_commands.MissingRole: "You are missing the role required to use this command.",
    app_commands.MissingAnyRole: "You are missing some roles required to use this command.",
    app_commands.MissingPermissions: "You are missing the required permissions to use this command.",
    app_commands.CheckFailure: "You are not allowed to use this command.",
    app_commands.CommandNotFound: "This command was not found.",
    app_commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
    app_commands.BotMissingPermissions: "The bot is missing the required permissions to use this command.",
    app_commands.CommandSignatureMismatch: "The command signature does not match: {error}",
    # commands
    commands.CommandError: "An error occurred: {error}",
    commands.CommandInvokeError: "A command invoke error occurred: {error}",
    commands.ConversionError: "An error occurred during conversion: {error}",
    commands.MissingRole: "You are missing the role required to use this command.",
    commands.MissingAnyRole: "You are missing some roles required to use this command.",
    commands.MissingPermissions: "You are missing the required permissions to use this command.",
    commands.CheckFailure: "You are not allowed to use this command.",
    commands.CommandNotFound: "This command was not found.",
    commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
    commands.BadArgument: "Invalid argument passed. Correct usage:\n```{ctx.command.usage}```",
    commands.MissingRequiredArgument: "Missing required argument. Correct usage:\n```{ctx.command.usage}```",
    commands.MissingRequiredAttachment: "Missing required attachment.",
    commands.NotOwner: "You are not the owner of this bot.",
    commands.BotMissingPermissions: "The bot is missing the required permissions to use this command.",
}


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.error_message = "An error occurred. Please try again later."
        bot.tree.error(self.dispatch_to_app_command_handler)

    async def dispatch_to_app_command_handler(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Dispatch command error to app_command_error event."""
        await self.on_app_command_error(interaction, error)

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle app command errors."""
        error_message = error_map.get(type(error), self.error_message).format(error=error)

        if interaction.response.is_done():
            await interaction.followup.send(error_message, ephemeral=True)
        else:
            await interaction.response.send_message(error_message, ephemeral=True)

        if type(error) not in error_map:
            self.log_error_traceback(error)

    @commands.Cog.listener()
    async def on_command_error(
        self, ctx: commands.Context[commands.Bot], error: commands.CommandError
    ):
        """Handle traditional command errors."""
        if isinstance(
            error,
            commands.UnexpectedQuoteError
            | commands.InvalidEndOfQuotedStringError
            | commands.CheckFailure,
        ):
            return  # Ignore these specific errors.

        error_message = error_map.get(type(error), self.error_message).format(error=error, ctx=ctx)

        await ctx.send(
            content=error_message,
            ephemeral=True,
        )

        if type(error) not in error_map:
            self.log_error_traceback(error)

    def log_error_traceback(self, error: Exception):
        """Helper method to log error traceback."""
        trace = traceback.format_exception(None, error, error.__traceback__)
        formatted_trace = "".join(trace)
        logger.error(f"Error: {error}\nTraceback:\n{formatted_trace}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ErrorHandler(bot))
