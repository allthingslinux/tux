import traceback

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

error_map: dict[type[Exception], str] = {
    # app_commands
    app_commands.AppCommandError: "An error occurred: {error}",
    app_commands.CommandInvokeError: "A command invoke error occurred: {error}",
    app_commands.TransformerError: "A transformer error occurred: {error}",
    app_commands.MissingRole: "User not in sudoers file. This incident will be reported. (Missing Role)",
    app_commands.MissingAnyRole: "User not in sudoers file. This incident will be reported. (Missing Roles)",
    app_commands.MissingPermissions: "User not in sudoers file. This incident will be reported. (Missing Permissions)",
    app_commands.CheckFailure: "User not in sudoers file. This incident will be reported. (Check Failure)",
    app_commands.CommandNotFound: "This command was not found.",
    app_commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
    app_commands.BotMissingPermissions: "User not in sudoers file. This incident will be reported. (Bot Missing Permissions)",
    app_commands.CommandSignatureMismatch: "The command signature does not match: {error}",
    # commands
    commands.CommandError: "An error occurred: {error}",
    commands.CommandInvokeError: "A command invoke error occurred: {error}",
    commands.ConversionError: "An error occurred during conversion: {error}",
    commands.MissingRole: "User not in sudoers file. This incident will be reported. (Missing Role)",
    commands.MissingAnyRole: "User not in sudoers file. This incident will be reported. (Missing Roles)",
    commands.MissingPermissions: "User not in sudoers file. This incident will be reported. (Missing Permissions)",
    commands.CheckFailure: "User not in sudoers file. This incident will be reported. (Permission Check Failed)",
    commands.CommandNotFound: "This command was not found.",
    commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
    commands.BadArgument: "Invalid argument passed. Correct usage: `{ctx.command.usage}`",
    commands.MissingRequiredArgument: "Missing required argument. Correct usage: `{ctx.command.usage}`",
    commands.MissingRequiredAttachment: "Missing required attachment.",
    commands.NotOwner: "User not in sudoers file. This incident will be reported. (Not Owner)",
    commands.BotMissingPermissions: "User not in sudoers file. This incident will be reported. (Bot Missing Permissions)",
}


class UnifiedErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.error_message = "An error occurred. Please try again later or contact support."
        # Attach the error handler if using app commands
        if hasattr(bot, "tree"):
            bot.tree.error(self.dispatch_to_app_command_handler)

    async def dispatch_to_app_command_handler(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Dispatch command error to appropriate handler."""
        await self.handle_app_command_error(interaction, error)

    async def handle_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ):
        """Handle errors for app commands."""
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
        """Handle errors for traditional commands."""
        if (
            hasattr(ctx.command, "on_error")
            or ctx.cog
            and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None
        ):
            return
        if isinstance(error, commands.CommandNotFound):
            return  # Optionally, provide feedback for unknown commands.
        error = getattr(error, "original", error)
        message: str = self.get_error_message(error, ctx)
        await ctx.send(content=message, ephemeral=False)
        if type(error) not in error_map:
            self.log_error_traceback(error)

    def get_error_message(
        self, error: Exception, ctx: commands.Context[commands.Bot] | None = None
    ) -> str:
        """Generate an error message from the error map."""
        if ctx:
            return error_map.get(type(error), self.error_message).format(error=error, ctx=ctx)
        return error_map.get(type(error), self.error_message).format(error=error)

    def log_error_traceback(self, error: Exception):
        """Helper method to log error traceback."""
        trace = traceback.format_exception(None, error, error.__traceback__)
        formatted_trace = "".join(trace)
        logger.error(f"Error: {error}\nTraceback:\n{formatted_trace}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UnifiedErrorHandler(bot))
