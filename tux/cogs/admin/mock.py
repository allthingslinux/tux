from typing import Any

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils import checks
from tux.utils.exceptions import AppCommandPermissionLevelError, PermissionLevelError


# Minimal Mock Objects for Required Arguments
class MockParameter:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"<MockParameter name='{self.name}'>"


class MockFlag:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self) -> str:
        return f"<MockFlag name='{self.name}'>"


# Generic Mock for objects needed by some discord.py exceptions
class MockObject:
    def __init__(self, **kwargs: Any):
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"<MockObject {attrs}>"


# Type Alias for the error structure in the dictionary
type ErrorStructure = tuple[type[Exception] | Any, tuple[Any, ...], dict[str, Any]]  # Allow Any for non-exception test

# Define Errors to Test - Expanded List with Dummy Data
# Derived from error_map in tux/handlers/error.py
ERRORS_TO_TEST: dict[str, ErrorStructure] = {
    # === Python Built-in / Unhandled ===
    "Unhandled Exception Test": (Exception, ("Generic Unhandled Exception Test",), {}),
    "ValueError": (ValueError, ("Test Value Error (Built-in)",), {}),
    "TypeError": (TypeError, ("Test Type Error (Built-in)",), {}),
    "AttributeError": (AttributeError, ("Test Attribute Error (Built-in)",), {}),
    "IndexError": (IndexError, ("Test Index Error (Built-in)",), {}),
    "KeyError": (KeyError, ("Test Key Error (Built-in)",), {}),
    "ZeroDivisionError": (ZeroDivisionError, ("Test Zero Division (Built-in)",), {}),
    "Non-Exception Test": ("This is a string, not an Exception", (), {}),  # Test non-exception handling
    # === discord.py API/Client Errors ===
    "discord.HTTPException": (
        discord.HTTPException,
        (MockObject(status=500, reason="Mock Internal Server Error"), "Mock HTTP Error"),
        {},
    ),  # Need response-like obj
    "discord.RateLimited": (discord.RateLimited, (15.5,), {}),  # retry_after
    "discord.Forbidden": (
        discord.Forbidden,
        (MockObject(status=403, reason="Mock Forbidden"), "Mock Forbidden Error"),
        {},
    ),
    "discord.NotFound": (
        discord.NotFound,
        (MockObject(status=404, reason="Mock Not Found"), "Mock Not Found Error"),
        {},
    ),
    "discord.DiscordServerError": (
        discord.DiscordServerError,
        (MockObject(status=502, reason="Mock Bad Gateway"), "Mock Server Error"),
        {},
    ),
    "discord.InvalidData": (discord.InvalidData, ("Mock Invalid Data Received",), {}),
    "discord.InteractionResponded": (
        discord.InteractionResponded,
        (MockObject(responded=True),),
        {},
    ),  # Needs interaction-like obj
    "discord.MissingApplicationID": (discord.MissingApplicationID, (), {}),
    # === discord.py Command Framework Errors (commands.*) ===
    "commands.CommandError": (commands.CommandError, ("Generic Command Error Test",), {}),
    "commands.CommandInvokeError": (
        commands.CommandInvokeError,
        (ValueError("Original error inside CommandInvokeError"),),
        {},
    ),  # Wraps another error
    "commands.ConversionError": (
        commands.ConversionError,
        (MockParameter("arg_that_failed_conv"), ValueError("Original Conversion Failure")),
        {},
    ),
    "commands.MissingRole (str)": (commands.MissingRole, ("RequiredRoleName",), {}),
    "commands.MissingRole (int)": (commands.MissingRole, (123456789012345678,), {}),
    "commands.MissingAnyRole": (commands.MissingAnyRole, ([123, "Another Role"],), {}),
    "commands.MissingPermissions": (commands.MissingPermissions, (["manage_messages", "kick_members"],), {}),
    "commands.FlagError": (commands.FlagError, ("Generic Flag Error (e.g., unexpected format)",), {}),
    "commands.BadFlagArgument": (
        commands.BadFlagArgument,
        (MockFlag("myflag"), ValueError("Invalid value for flag")),
        {},
    ),
    "commands.MissingRequiredFlag": (commands.MissingRequiredFlag, (MockFlag("required_flag"),), {}),
    "commands.CheckFailure": (commands.CheckFailure, ("Generic Check Failure Test",), {}),
    "commands.CommandOnCooldown": (
        commands.CommandOnCooldown,
        (commands.Cooldown(1, 15.0), 11.99),  # type: ignore
        {},
    ),
    "commands.MissingRequiredArgument": (commands.MissingRequiredArgument, (MockParameter("needed_arg"),), {}),
    "commands.TooManyArguments": (commands.TooManyArguments, ("Too Many Arguments Test",), {}),
    "commands.NotOwner": (commands.NotOwner, ("Not Owner Check Test",), {}),
    "commands.BotMissingPermissions": (commands.BotMissingPermissions, (["send_messages", "embed_links"],), {}),
    "commands.BadArgument": (commands.BadArgument, ("Generic Bad Argument Test",), {}),
    "commands.MemberNotFound": (commands.MemberNotFound, ("NonExistentMember#1234",), {}),
    "commands.UserNotFound": (commands.UserNotFound, ("UnknownUser#5678",), {}),
    "commands.ChannelNotFound": (commands.ChannelNotFound, ("#non-existent-channel",), {}),
    "commands.RoleNotFound": (commands.RoleNotFound, ("@UnknownRole",), {}),
    "commands.EmojiNotFound": (commands.EmojiNotFound, (":unknown_emoji:",), {}),
    "commands.GuildNotFound": (commands.GuildNotFound, ("InvalidGuildID123",), {}),
    "commands.CommandNotFound": (
        commands.CommandNotFound,
        ("test_command_not_found",),
        {},
    ),  # Usually ignored by handler
    # === discord.py App Command Errors (app_commands.*) ===
    "app_commands.AppCommandError": (app_commands.AppCommandError, ("Generic App Command Error Test",), {}),
    "app_commands.CommandInvokeError": (
        app_commands.CommandInvokeError,
        (ValueError("Original error inside AppCommandInvokeError"),),
        {},
    ),  # Wraps another error
    "app_commands.TransformerError": (
        app_commands.TransformerError,
        ("Transformer failed", discord.AppCommandOptionType.string, type("MyTransformer", (), {})),
        {},
    ),  # Simplified args
    "app_commands.MissingRole (str)": (app_commands.MissingRole, ("RequiredAppNameRole",), {}),
    "app_commands.MissingRole (int)": (app_commands.MissingRole, (987654321098765432,), {}),
    "app_commands.MissingAnyRole": (app_commands.MissingAnyRole, ([987, "Another App Role"],), {}),
    "app_commands.MissingPermissions": (app_commands.MissingPermissions, (["app_perm1", "app_perm2"],), {}),
    "app_commands.CheckFailure": (app_commands.CheckFailure, ("Generic App Check Failure Test",), {}),
    "app_commands.CommandOnCooldown": (
        app_commands.CommandOnCooldown,
        (app_commands.Cooldown(1, 10.0), 7.54),
        {},
    ),  # Needs cooldown obj and retry_after
    "app_commands.BotMissingPermissions": (
        app_commands.BotMissingPermissions,
        (["app_bot_perm1", "app_bot_perm2"],),
        {},
    ),
    "app_commands.CommandSignatureMismatch": (app_commands.CommandSignatureMismatch, ("Signature Mismatch Test",), {}),
    # === Custom Errors (from tux.utils.exceptions) ===
    "Custom PermissionLevelError": (PermissionLevelError, ("Req Level 5 (Admin)",), {}),
    "Custom AppCommandPermissionLevelError": (AppCommandPermissionLevelError, ("Req Level 6 (Head Admin)",), {}),
}

# --- New Command Structure --- #


# Autocomplete function for the error type
async def error_type_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    choices = [name for name in ERRORS_TO_TEST if current.lower() in name.lower()]
    return [app_commands.Choice(name=choice, value=choice) for choice in choices[:25]]  # Limit to 25 choices


class Mock(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.hybrid_group(name="mock", description="Commands to mock bot behaviors for testing.")
    @checks.has_pl(level=8)
    async def mock(self, ctx: commands.Context[Tux]) -> None:
        """
        Base command group for mocking various bot behaviors.
        Requires System Administrator permissions (Level 8).
        """
        # Send help if no subcommand is invoked
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @mock.command(name="error", description="Raise a specified error for testing error handling.")
    @app_commands.autocomplete(error_type=error_type_autocomplete)
    @checks.has_pl(level=8)  # Apply check to subcommand as well
    async def mock_error(self, ctx: commands.Context[Tux], *, error_type: str):
        """
        Raises a specified error to test the global error handler.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command invocation context.
        error_type : str
            The name of the error to raise (use autocomplete).

        This command intentionally raises various exceptions based on the input.
        These exceptions will propagate up to the global ErrorHandler cog.
        Requires System Administrator permissions (Level 8).
        """

        error_info = ERRORS_TO_TEST.get(error_type)
        if not error_info:
            valid_keys = ", ".join(f"`{k}`" for k in ERRORS_TO_TEST)
            # Check if interaction or context to send ephemeral message
            if isinstance(ctx.interaction, discord.Interaction):
                await ctx.interaction.response.send_message(
                    f"Error type '{error_type}' not found. Valid types are: {valid_keys}",
                    ephemeral=True,
                )
            else:
                await ctx.send(
                    f"Error type '{error_type}' not found. Valid types are: {valid_keys}",
                )  # Cannot be ephemeral here
            return

        error_class, error_args, error_kwargs = error_info

        # Log intention and raise the error
        logger.info(f"Admin '{ctx.author}' requested raising mocked error: {error_type}")

        raise error_class(*error_args, **error_kwargs)  # type: ignore


async def setup(bot: Tux) -> None:
    await bot.add_cog(Mock(bot))
