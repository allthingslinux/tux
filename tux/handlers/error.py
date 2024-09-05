import traceback

import discord
import sentry_sdk
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils.embeds import EmbedCreator
from tux.utils.exceptions import AppCommandPermissionLevelError, PermissionLevelError

"""
Exception
    DiscordException
        GatewayNotFound
        ClientException
            CommandRegistrationError
            InvalidData
            LoginFailure
            ConnectionClosed
            PrivilegedIntentsRequired
            InteractionResponded
        HTTPException
            Forbidden
            NotFound
            DiscordServerError
            app_commands.CommandSyncFailure
        RateLimited
        CommandError
            ConversionError
            UserInputError
                MissingRequiredArgument
                MissingRequiredAttachment
                TooManyArguments
                BadArgument
                    MessageNotFound
                    MemberNotFound
                    GuildNotFound
                    UserNotFound
                    ChannelNotFound
                    ChannelNotReadable
                    BadColourArgument
                    RoleNotFound
                    BadInviteArgument
                    EmojiNotFound
                    GuildStickerNotFound
                    ScheduledEventNotFound
                    PartialEmojiConversionFailure
                    BadBoolArgument
                    RangeError
                    ThreadNotFound
                    FlagError
                        BadFlagArgument
                        MissingFlagArgument
                        TooManyFlags
                        MissingRequiredFlag
                    BadUnionArgument
                    BadLiteralArgument
                    ArgumentParsingError
                        UnexpectedQuoteError
                        InvalidEndOfQuotedStringError
                        ExpectedClosingQuoteError
                CommandNotFound
                CheckFailure
                    CheckAnyFailure
                    PrivateMessageOnly
                    NoPrivateMessage
                    NotOwner
                    MissingPermissions
                    BotMissingPermissions
                    MissingRole
                    BotMissingRole
                    MissingAnyRole
                    BotMissingAnyRole
                    NSFWChannelRequired
                DisabledCommand
                CommandInvokeError
                CommandOnCooldown
                MaxConcurrencyReached
                HybridCommandError
            ExtensionError
                ExtensionAlreadyLoaded
                ExtensionNotLoaded
                NoEntryPointError
                ExtensionFailed
                ExtensionNotFound
        AppCommandError
            CommandInvokeError
            TransformerError
            TranslationError
            CheckFailure
                NoPrivateMessage
                MissingRole
                MissingAnyRole
                MissingPermissions
                BotMissingPermissions
                CommandOnCooldown
            CommandLimitReached
            CommandAlreadyRegistered
            CommandSignatureMismatch
            CommandNotFound
            MissingApplicationID
            CommandSyncFailure
        HTTPException
            CommandSyncFailure
"""


error_map: dict[type[Exception], str] = {
    # app_commands
    app_commands.AppCommandError: "An error occurred: {error}",
    app_commands.CommandInvokeError: "A command invoke error occurred: {error}",
    app_commands.TransformerError: "A transformer error occurred: {error}",
    app_commands.MissingRole: "User not in sudoers file. This incident will be reported. (Missing Role)",
    app_commands.MissingAnyRole: "User not in sudoers file. This incident will be reported. (Missing Roles)",
    app_commands.MissingPermissions: "User not in sudoers file. This incident will be reported. (Missing Permissions)",
    app_commands.CheckFailure: "User not in sudoers file. This incident will be reported. (Permission Check Failed)",
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
    commands.FlagError: "An error occurred with the flags:\n`{error}`",
    commands.MissingRequiredFlag: "Missing argument: {error}. Correct usage:\n`{ctx.prefix}{ctx.command.usage}`",
    commands.CheckFailure: "User not in sudoers file. This incident will be reported. (Permission Check Failed)",
    commands.CommandOnCooldown: "This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
    commands.MissingRequiredArgument: "Missing required argument. Correct usage:\n`{ctx.prefix}{ctx.command.usage}`",
    commands.TooManyArguments: "Too many arguments passed. Correct usage:\n`{ctx.prefix}{ctx.command.usage}`",
    commands.NotOwner: "User not in sudoers file. This incident will be reported. (Not Owner)",
    commands.BotMissingPermissions: "User not in sudoers file. This incident will be reported. (Bot Missing Permissions)",
    # Custom errors
    PermissionLevelError: "User not in sudoers file. This incident will be reported. (Missing required permission: {error.permission})",
    AppCommandPermissionLevelError: "User not in sudoers file. This incident will be reported. (Missing required permission: {error.permission})",
}


class ErrorHandler(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.error_message = "An error occurred. Please try again later or contact support."

    async def cog_load(self):
        # Set a global error handler for application commands
        tree = self.bot.tree
        self._old_tree_error = tree.on_error
        tree.on_error = self.on_app_command_error

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """
        Handle errors for application commands.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        error : app_commands.AppCommandError
            The error that occurred.
        """

        error_message = error_map.get(type(error), self.error_message).format(error=error)

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            description=error_message,
        )

        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=30)

        if type(error) in error_map:
            sentry_sdk.capture_exception(error)
        else:
            self.log_error_traceback(error)

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context[Tux],
        error: commands.CommandError | commands.CheckFailure,
    ) -> None:
        """
        Handle errors for traditional prefix commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        error : commands.CommandError | commands.CheckFailure
            The error that occurred.
        """

        # If the command has its own error handler, return
        # if hasattr(ctx.command, "on_error"):
        #     logger.debug(f"Command {ctx.command} has its own error handler.")
        #     return

        # If the cog has its own error handler, return
        # if ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
        #     logger.debug(f"Cog {ctx.cog} has its own error handler.")
        #     return

        if isinstance(error, commands.CheckFailure):
            message = error_map.get(type(error), self.error_message).format(error=error, ctx=ctx)
            # await ctx.send(content=message, ephemeral=True, delete_after=30)
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                description=message,
            )
            await ctx.send(embed=embed, ephemeral=True, delete_after=30)
            sentry_sdk.capture_exception(error)
            return

        # If the error is CommandNotFound, return
        if isinstance(
            error,
            commands.CommandNotFound,
        ):
            return

        # Check for original error raised and sent to CommandInvokeError
        error = getattr(error, "original", error)

        # Get the error message and send it to the user
        message: str = self.get_error_message(error, ctx)

        # await ctx.send(content=message, ephemeral=True, delete_after=30)

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            description=message,
        )
        await ctx.send(embed=embed, ephemeral=True, delete_after=30)

        # Log the error traceback if it's not in the error map
        if type(error) not in error_map:
            self.log_error_traceback(error)
        else:
            sentry_sdk.capture_exception(error)

    def get_error_message(
        self,
        error: Exception,
        ctx: commands.Context[Tux] | None = None,
    ) -> str:
        """
        Get the error message for a given error.

        Parameters
        ----------
        error : Exception
            The error that occurred.
        ctx : commands.Context[Tux], optional
            The discord context object, by default None
        """
        if ctx:
            return error_map.get(type(error), self.error_message).format(error=error, ctx=ctx)

        return error_map.get(type(error), self.error_message).format(error=error)

    def log_error_traceback(self, error: Exception) -> None:
        """
        Log the error traceback.

        Parameters
        ----------
        error : Exception
            The error that occurred
        """
        trace = traceback.format_exception(None, error, error.__traceback__)
        formatted_trace = "".join(trace)
        logger.error(f"Error: {error}\nTraceback:\n{formatted_trace}")
        sentry_sdk.capture_exception(error)


async def setup(bot: Tux) -> None:
    await bot.add_cog(ErrorHandler(bot))
