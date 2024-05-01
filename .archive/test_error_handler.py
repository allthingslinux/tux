
"""A Cog dedicated to raise every discord.py error on command with the purpose of testing error handling."""

import discord
from discord.ext import commands
from discord.ext.commands import Context, Bot, Cog

""" Command Errors:
        https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#exception-hierarchy

        ConversionError
        UserInputError
            MissingRequiredArgument
            TooManyArguments
            BadArgument
                MessageNotFound
                MemberNotFound
                UserNotFound
                ChannelNotFound
                ChannelNotReadable
                BadColourArgument
                RoleNotFound
                BadInviteArgument
                EmojiNotFound
                PartialEmojiConversionFailure
                BadBoolArgument
            BadUnionArgument
            ArgumentParsingError
        CommandNotFound
        CheckFailure
            BotMissingPermissions
            BotMissingRole
            BotMissingAnyRole
            MissingPermission
            MissingRole
            MissingAnyRole
            CheckAnyFailure
            NotOwner
            NoPrivateMessage
            PrivateMessageOnly
            NSFWChannelRequired
        DisabledCommand
        CommandInvokeError
        CommandOnCooldown
        MaxConcurrencyReached
    """


class ErrorTests(Cog):
    """For Testing Error Handling"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @discord.ext.commands.group(name="error", aliases=["err"])
    async def test_error(self, ctx: Context):
        """Group of commands to raise errors for every type of discord.py error"""
        if ctx.invoked_subcommand is None:
            # Send the help command for this group
            await ctx.send_help(ctx.command)

    @test_error.command(name="DiscordException")
    async def discord_exception(self, ctx: Context):
        """Base exception class for discord.py"""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.DiscordException
        raise discord.DiscordException()

    @test_error.command(name="CommandError")
    async def CommandError(self, ctx, message=None, *args: object):
        """The base exception type for all command related errors."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CommandError
        raise commands.CommandError(message, *args)

    @test_error.command(name="ConversionError")
    async def ConversionError(self, ctx, converter, original):
        """Exception raised when a Converter class raises non-CommandError."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ConversionError
        raise commands.ConversionError(converter, original)

    @test_error.command(name="UserInputError")
    async def user_input_error(self, ctx: Context):
        """The base exception type for errors that involve errors regarding user input."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.UserInputError
        raise commands.UserInputError()

    @test_error.command(name="MissingRequiredArgument")
    async def missing_required_argument(self, ctx: Context):
        """Exception raised when parsing a command and a parameter that is required is not encountered."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MissingRequiredArgument
        raise commands.MissingRequiredArgument()

    @test_error.command(name="TooManyArguments")
    async def too_many_arguments(self, ctx: Context):
        """Exception raised when the command was passed too many arguments and its Command.ignore_extra attribute was not set to True."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.TooManyArguments
        raise commands.TooManyArguments()

    @test_error.command(name="BadArgument")
    async def bad_argument(self, ctx: Context):
        """Exception raised when a parsing or conversion failure is encountered on an argument to pass into a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadArgument
        raise commands.BadArgument()

    @test_error.command(name="MessageNotFound")
    async def message_not_found(self, ctx: Context):
        """Exception raised when the message provided was not found in the channel."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MessageNotFound
        raise commands.MessageNotFound()

    @test_error.command(name="MemberNotFound")
    async def member_not_found(self, ctx: Context):
        """Exception raised when the member provided was not found in the bot’s cache."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MemberNotFound
        raise commands.MemberNotFound()

    @test_error.command(name="UserNotFound")
    async def user_not_found(self, ctx: Context):
        """Exception raised when the user provided was not found in the bot’s cache."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.UserNotFound
        raise commands.UserNotFound()

    @test_error.command(name="ChannelNotFound")
    async def channel_not_found(self, ctx: Context):
        """Exception raised when the bot can not find the channel."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ChannelNotFound
        raise commands.ChannelNotFound()

    @test_error.command(name="ChannelNotReadable")
    async def channel_not_readable(self, ctx: Context):
        """Exception raised when the bot does not have permission to read messages in the channel."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ChannelNotReadable
        raise commands.ChannelNotReadable()

    @test_error.command(name="BadColourArgument")
    async def bad_colour_argument(self, ctx: Context):
        """Exception raised when the colour is not valid."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadColourArgument
        raise commands.BadColourArgument()

    @test_error.command(name="RoleNotFound")
    async def role_not_found(self, ctx: Context):
        """Exception raised when the bot can not find the role."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.RoleNotFound
        raise commands.RoleNotFound()

    @test_error.command(name="BadInviteArgument")
    async def bad_invite_argument(self, ctx: Context):
        """Exception raised when the invite is invalid or expired."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadInviteArgument
        raise commands.BadInviteArgument()

    @test_error.command(name="EmojiNotFound")
    async def emoji_not_found(self, ctx: Context):
        """Exception raised when the bot can not find the emoji."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.EmojiNotFound
        raise commands.EmojiNotFound()

    @test_error.command(name="PartialEmojiConversionFailure")
    async def partial_emoji_conversion_failure(self, ctx: Context):
        """Exception raised when the emoji provided does not match the correct format."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.PartialEmojiConversionFailure
        raise commands.PartialEmojiConversionFailure()

    @test_error.command(name="BadUnionArgument")
    async def bad_union_argument(self, ctx: Context):
        """Exception raised when a typing.Union converter fails for all its associated types."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BadUnionArgument
        raise commands.BadUnionArgument()

    @test_error.command(name="ArgumentParsingError")
    async def argument_parsing_error(self, ctx: Context):
        """An exception raised when the parser fails to parse a user’s input."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ArgumentParsingError
        raise commands.ArgumentParsingError()

    @test_error.command(name="UnexpectedQuoteError")
    async def unexpected_quote_error(self, ctx: Context):
        """An exception raised when the parser encounters a quote mark inside a non-quoted string."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.UnexpectedQuoteError
        raise commands.UnexpectedQuoteError()

    @test_error.command(name="InvalidEndOfQuotedStringError")
    async def invalid_end_of_quoted_string_error(self, ctx: Context):
        """An exception raised when a space is expected after the closing quote in a string but a different character is found."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.InvalidEndOfQuotedStringError
        raise commands.InvalidEndOfQuotedStringError()

    @test_error.command(name="ExpectedClosingQuoteError")
    async def expected_closing_quote_error(self, ctx: Context):
        """An exception raised when a quote character is expected but not found."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExpectedClosingQuoteError
        raise commands.ExpectedClosingQuoteError()

    @test_error.command(name="CommandNotFound")
    async def command_not_found(self, ctx: Context):
        """Exception raised when a command is attempted to be invoked but no command under that name is found."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CommandNotFound
        raise commands.CommandNotFound()

    @test_error.command(name="CheckFailure")
    async def check_failure(self, ctx: Context):
        """Exception raised when the predicates in Command.checks have failed."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CheckFailure
        raise commands.CheckFailure()

    @test_error.command(name="CheckAnyFailure")
    async def check_any_failure(self, ctx: Context):
        """Exception raised when all predicates in check_any() fail."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CheckAnyFailure
        raise commands.CheckAnyFailure()

    @test_error.command(name="PrivateMessageOnly")
    async def private_message_only(self, ctx: Context):
        """Exception raised when an operation does not work outside of private message contexts."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.PrivateMessageOnly
        raise commands.PrivateMessageOnly()

    @test_error.command(name="NoPrivateMessage")
    async def no_private_message(self, ctx: Context):
        """Exception raised when an operation does not work in private message contexts."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NoPrivateMessage
        raise commands.NoPrivateMessage()

    @test_error.command(name="NotOwner")
    async def not_owner(self, ctx: Context):
        """Exception raised when the message author is not the owner of the bot."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NotOwner
        raise commands.NotOwner()

    @test_error.command(name="MissingPermissions")
    async def missing_permissions(self, ctx: Context):
        """Exception raised when the command invoker lacks permissions to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MissingPermissions
        raise commands.MissingPermissions()

    @test_error.command(name="BotMissingPermissions")
    async def _bot_missing_permissions(self, ctx: Context):
        """Exception raised when the bot’s member lacks permissions to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BotMissingPermissions
        raise commands.BotMissingPermissions()

    @test_error.command(name="MissingRole")
    async def missing_role(self, ctx: Context):
        """Exception raised when the command invoker lacks a role to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MissingRole
        raise commands.MissingRole()

    @test_error.command(name="BotMissingRole")
    async def _bot_missing_role(self, ctx: Context):
        """Exception raised when the bot’s member lacks a role to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BotMissingRole
        raise commands.BotMissingRole()

    @test_error.command(name="MissingAnyRole")
    async def missing_any_role(self, ctx: Context):
        """Exception raised when the command invoker lacks any of the roles specified to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MissingAnyRole
        raise commands.MissingAnyRole()

    @test_error.command(name="BotMissingAnyRole")
    async def _bot_missing_any_role(self, ctx: Context):
        """Exception raised when the bot’s member lacks any of the roles specified to run a command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.BotMissingAnyRole
        raise commands.BotMissingAnyRole()

    @test_error.command(name="NSFWChannelRequired")
    async def nsfw_hannel_required(self, ctx: Context):
        """Exception raised when a channel does not have the required NSFW setting."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NSFWChannelRequired
        raise commands.NSFWChannelRequired()

    @test_error.command(name="DisabledCommand")
    async def disabled_command(self, ctx: Context):
        """Exception raised when the command being invoked is disabled."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.DisabledCommand
        raise commands.DisabledCommand()

    @test_error.command(name="CommandInvokeError")
    async def command_invoke_error(self, ctx: Context):
        """Exception raised when the command being invoked raised an exception."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CommandInvokeError
        raise commands.CommandInvokeError()

    @test_error.command(name="CommandOnCooldown")
    async def command_on_cooldown(self, ctx: Context):
        """Exception raised when the command being invoked is on cooldown."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CommandOnCooldown
        raise commands.CommandOnCooldown()

    @test_error.command(name="MaxConcurrencyReached")
    async def max_concurrency_reached(self, ctx: Context):
        """Exception raised when the command being invoked has reached its maximum concurrency."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.MaxConcurrencyReached
        raise commands.MaxConcurrencyReached()

    @test_error.command(name="ExtensionError")
    async def extension_error(self, ctx: Context):
        """Base exception for extension related errors."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExtensionError
        raise commands.ExtensionError()

    @test_error.command(name="ExtensionAlreadyLoaded")
    async def extension_already_loaded(self, ctx: Context):
        """An exception raised when an extension has already been loaded."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExtensionAlreadyLoaded
        raise commands.ExtensionAlreadyLoaded()

    @test_error.command(name="ExtensionNotLoaded")
    async def extension_not_loaded(self, ctx: Context):
        """An exception raised when an extension was not loaded."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExtensionNotLoaded
        raise commands.ExtensionNotLoaded()

    @test_error.command(name="NoEntryPointError")
    async def no_entry_point_error(self, ctx: Context):
        """An exception raised when an extension does not have a setup entry point function."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.NoEntryPointError
        raise commands.NoEntryPointError()

    @test_error.command(name="ExtensionFailed")
    async def extension_failed(self, ctx: Context):
        """An exception raised when an extension failed to load during execution of the module or setup entry point."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExtensionFailed
        raise commands.ExtensionFailed()

    @test_error.command(name="ExtensionNotFound")
    async def extension_not_found(self, ctx: Context):
        """An exception raised when an extension is not found."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.ExtensionNotFound
        raise commands.ExtensionNotFound()

    @test_error.command(name="ClientException")
    async def client_exception(self, ctx: Context):
        """Exception that’s thrown when an operation in the Client fails."""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.ClientException
        raise discord.ClientException()

    @test_error.command(name="CommandRegistrationError")
    async def command_registration_error(self, ctx: Context):
        """An exception raised when the command can’t be added because the name is already taken by a different command."""
        # https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#discord.ext.commands.CommandRegistrationError
        raise commands.CommandRegistrationError()


async def setup(bot: Bot) -> None:
    """Load the ErrorTests cog."""
    await bot.add_cog(ErrorTests(bot))
    print("Cog loaded: ErrorTests")
