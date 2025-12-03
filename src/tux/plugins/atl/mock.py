"""
Mock Plugin for Tux Bot.

This plugin provides error testing and debugging functionality,
allowing developers to trigger various error conditions and test
error handling mechanisms in the bot.
"""

import asyncio
from typing import Any

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.services.handlers.error.formatter import ERROR_CONFIG_MAP
from tux.shared.config import CONFIG
from tux.ui.embeds import EmbedCreator


# Minimal Mock Objects for Required Arguments
class MockParameter:
    """Mock parameter object for testing purposes."""

    def __init__(self, name: str):
        """Initialize a mock parameter.

        Parameters
        ----------
        name : str
            The name of the parameter.
        """
        self.name = name

    def __repr__(self) -> str:
        """Return string representation of the mock parameter.

        Returns
        -------
        str
            String representation.
        """
        return f"<MockParameter name='{self.name}'>"


class MockFlag:
    """Mock flag object for testing purposes."""

    def __init__(self, name: str):
        """Initialize a mock flag.

        Parameters
        ----------
        name : str
            The name of the flag.
        """
        self.name = name

    def __repr__(self) -> str:
        """Return string representation of the mock flag.

        Returns
        -------
        str
            String representation.
        """
        return f"<MockFlag name='{self.name}'>"


class MockObject:
    """A simple mock object that accepts arbitrary attributes."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the mock object with arbitrary attributes.

        Parameters
        ----------
        **kwargs : Any
            Arbitrary keyword arguments to set as attributes.
        """
        self.__dict__.update(kwargs)

    def __repr__(self) -> str:
        """
        Return a string representation of the mock object.

        Returns
        -------
        str
            String representation showing all attributes.
        """
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"<MockObject {attrs}>"


class ErrorTestDefinition:
    """Defines how to construct and test a specific error type."""

    def __init__(
        self,
        error_class: type[Exception],
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        description: str = "",
        category: str = "General",
    ) -> None:
        """Initialize an error test definition.

        Parameters
        ----------
        error_class : type[Exception]
            The exception class to test.
        args : tuple[Any, ...], optional
            Positional arguments for error construction.
        kwargs : dict[str, Any] | None, optional
            Keyword arguments for error construction.
        description : str, optional
            Description of the error test.
        category : str, optional
            Category for organizing error tests.
        """
        self.error_class = error_class
        self.args = args
        self.kwargs = kwargs or {}
        self.description = description
        self.category = category
        self.name = error_class.__name__

    def create_error(self) -> Exception:
        """
        Create an instance of this error for testing.

        Returns
        -------
        Exception
            An instance of the configured error class.
        """
        return self.error_class(*self.args, **self.kwargs)

    def get_config(self) -> dict[str, Any] | None:
        """
        Get the error handler configuration for this error type.

        Returns
        -------
        dict[str, Any] | None
            Error handler configuration dict, or None if not configured.
        """
        if not (config := ERROR_CONFIG_MAP.get(self.error_class)):
            return None

        return {
            "message_format": config.message_format,
            "send_to_sentry": config.send_to_sentry,
            "log_level": config.log_level,
            "has_detail_extractor": config.detail_extractor is not None,
            "suggest_similar_commands": config.suggest_similar_commands,
        }


class ErrorTestRegistry:
    """Dynamic registry of errors that can be tested, based on the actual error handler."""

    def __init__(self) -> None:
        """Initialize the error test registry."""
        self.tests: dict[str, ErrorTestDefinition] = {}
        self._build_test_registry()

    def _build_test_registry(self) -> None:  # noqa: PLR0912, PLR0915
        """Build test cases dynamically from ERROR_CONFIG_MAP."""
        # Build all tests from ERROR_CONFIG_MAP - this keeps us perfectly in sync
        for error_type in ERROR_CONFIG_MAP:
            name = error_type.__name__

            # Determine category based on exception hierarchy and functionality
            if error_type.__module__.startswith("discord.app_commands"):
                category = "Application Commands"
                self._add_app_command_test(error_type)
            elif error_type.__module__.startswith("discord.ext.commands"):
                # Sub-categorize traditional command errors
                if name in [
                    "CheckFailure",
                    "CheckAnyFailure",
                    "PrivateMessageOnly",
                    "NoPrivateMessage",
                    "NotOwner",
                    "NSFWChannelRequired",
                ]:
                    category = "Check Failures"
                elif name in [
                    "FlagError",
                    "BadFlagArgument",
                    "MissingRequiredFlag",
                    "MissingFlagArgument",
                    "TooManyFlags",
                ]:
                    category = "Flag Errors"
                elif name.startswith("Extension") or name in [
                    "NoEntryPointError",
                    "CommandRegistrationError",
                    "HybridCommandError",
                ]:
                    category = "Extension Management"
                elif "NotFound" in name and name.endswith("NotFound"):
                    category = "Entity Not Found"
                else:
                    category = "Traditional Commands"
                self._add_traditional_command_test(error_type)
            elif error_type.__module__ == "discord" or error_type.__module__.startswith(
                "discord.",
            ):
                # Sub-categorize Discord API errors
                if name in [
                    "ConnectionClosed",
                    "GatewayNotFound",
                    "InvalidData",
                    "LoginFailure",
                    "PrivilegedIntentsRequired",
                    "InteractionResponded",
                    "MissingApplicationID",
                ]:
                    category = "Client Connection"
                else:
                    category = "Discord API"
                self._add_discord_api_test(error_type)
            elif error_type.__module__.startswith("httpx"):
                category = "HTTPX Errors"
                self._add_httpx_test(error_type)
            elif name.startswith("Tux"):
                category = "Custom Errors"
                self._add_custom_test(error_type)
            else:
                category = "Base Exceptions"
                self._add_builtin_test(error_type)

        # Ensure ALL exceptions from ERROR_CONFIG_MAP have a test case
        # This handles any exceptions that might not have been caught by the module-based logic above
        configured_exceptions = set(ERROR_CONFIG_MAP.keys())
        tested_exceptions = {test_def.error_class for test_def in self.tests.values()}

        missing_exceptions = configured_exceptions - tested_exceptions
        for error_type in missing_exceptions:
            name = error_type.__name__
            module = error_type.__module__

            # Determine category for missing exceptions
            if module.startswith("discord.app_commands"):
                category = "Application Commands"
            elif module.startswith("discord.ext.commands"):
                if name in [
                    "CheckFailure",
                    "CheckAnyFailure",
                    "PrivateMessageOnly",
                    "NoPrivateMessage",
                    "NotOwner",
                    "NSFWChannelRequired",
                ]:
                    category = "Check Failures"
                elif "NotFound" in name and name.endswith("NotFound"):
                    category = "Entity Not Found"
                else:
                    category = "Traditional Commands"
            elif module.startswith("discord"):
                category = "Discord API"
            elif module.startswith("httpx"):
                category = "HTTPX Errors"
            elif name.startswith("Tux"):
                category = "Custom Errors"
            else:
                category = "Base Exceptions"

            # Create a basic test case for any missing exception
            try:
                # Use module-qualified name to avoid conflicts
                key = f"{module}.{name}"
                self.tests[key] = ErrorTestDefinition(
                    error_type,
                    (),  # No args
                    {},  # No kwargs
                    f"Mock {name.lower().replace('error', ' error')}",
                    category,
                )
            except Exception:
                # If we can't create a test, skip it
                continue

    def _add_test(
        self,
        name: str,
        error_class: type[Exception],
        args: tuple[Any, ...] = (),
        description: str = "",
        category: str = "General",
    ) -> None:
        """Add a test case to the registry."""
        # Handle duplicate exception names by using module-qualified names as keys
        key = name
        if name in self.tests:
            # If this name already exists, use module-qualified name
            key = f"{error_class.__module__}.{name}"

        self.tests[key] = ErrorTestDefinition(
            error_class,
            args,
            {},
            description,
            category,
        )

    def _add_app_command_test(self, error_type: type[Exception]) -> None:
        """Add app command specific test cases."""
        name = error_type.__name__

        # Specific mappings for app command errors
        specific_mappings = {
            app_commands.CommandInvokeError: (
                "App command wrapping another error",
                (ValueError("Original error inside app command"),),
            ),
            app_commands.TransformerError: (
                "App command argument transformation failed",
                (
                    "Transformer failed",
                    discord.AppCommandOptionType.string,
                    type("MockTransformer", (), {}),
                ),
            ),
            app_commands.MissingAnyRole: (
                "App command missing any of multiple roles",
                ([987654321, "AnotherRole"],),
            ),
            app_commands.MissingPermissions: (
                "App command missing permissions",
                (["manage_messages", "kick_members"],),
            ),
            app_commands.CommandOnCooldown: (
                "App command on cooldown",
                (app_commands.Cooldown(1, 10.0), 7.54),
            ),
            app_commands.BotMissingPermissions: (
                "Bot missing permissions for app command",
                (["send_messages", "embed_links"],),
            ),
        }

        if error_type in specific_mappings:
            description, args = specific_mappings[error_type]
            self.tests[name] = ErrorTestDefinition(
                error_type,
                args,
                {},
                description,
                "Application Commands",
            )
        elif error_type == app_commands.MissingRole:
            self.tests[f"{name}_str"] = ErrorTestDefinition(
                error_type,
                ("RequiredAppRole",),
                {},
                "App command missing role (by name)",
                "App Commands",
            )
            self.tests[f"{name}_int"] = ErrorTestDefinition(
                error_type,
                (123456789012345678,),
                {},
                "App command missing role (by ID)",
                "App Commands",
            )
        elif hasattr(error_type, "__name__"):
            realistic_args = self._get_realistic_app_command_args(name)
            self.tests[name] = ErrorTestDefinition(
                error_type,
                realistic_args,
                {},
                f"App command {name.lower().replace('error', ' error')}",
                "Application Commands",
            )

    def _get_realistic_app_command_args(self, error_name: str) -> tuple[Any, ...]:
        """
        Get realistic arguments for app command errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the error type.
        """
        error_name_lower = error_name.lower()

        # Use mapping instead of multiple if statements
        arg_mappings = {
            ("command", "not"): ("/nonexistent_command",),
            ("command",): ("/mock error",),
            ("check",): ("Permission check failed",),
            ("transform", "convert"): ("invalid_input",),
        }

        return next(
            (
                args
                for keywords, args in arg_mappings.items()
                if all(keyword in error_name_lower for keyword in keywords)
            ),
            (f"app_command_{error_name_lower}_example",),
        )

    def _add_traditional_command_test(self, error_type: type[Exception]) -> None:
        """Add traditional command specific test cases."""
        name = error_type.__name__

        # Determine category based on exception name
        category = "Traditional Commands"
        if name in [
            "CheckFailure",
            "CheckAnyFailure",
            "PrivateMessageOnly",
            "NoPrivateMessage",
            "NotOwner",
            "NSFWChannelRequired",
        ]:
            category = "Check Failures"
        elif name in [
            "FlagError",
            "BadFlagArgument",
            "MissingRequiredFlag",
            "MissingFlagArgument",
            "TooManyFlags",
        ]:
            category = "Flag Errors"
        elif name.startswith("Extension") or name in [
            "NoEntryPointError",
            "CommandRegistrationError",
            "HybridCommandError",
        ]:
            category = "Extension Management"
        elif "NotFound" in name and name.endswith("NotFound"):
            category = "Entity Not Found"

        # Specific mappings for traditional command errors
        specific_mappings = {
            commands.CommandInvokeError: (
                "Traditional command wrapping another error",
                (ValueError("Original error inside traditional command"),),
            ),
            commands.ConversionError: (
                "Traditional command argument conversion failed",
                (MockParameter("failed_param"), ValueError("Conversion failed")),
            ),
            commands.MissingAnyRole: (
                "Traditional command missing any of multiple roles",
                ([123456789, "AnotherRole"],),
            ),
            commands.MissingPermissions: (
                "Traditional command missing permissions",
                (["manage_guild", "ban_members"],),
            ),
            commands.FlagError: (
                "Traditional command flag error",
                ("Generic flag parsing error",),
            ),
            commands.BadFlagArgument: (
                "Traditional command bad flag argument",
                (MockFlag("test_flag"), ValueError("Invalid flag value")),
            ),
            commands.MissingRequiredFlag: (
                "Traditional command missing required flag",
                (MockFlag("required_flag"),),
            ),
            commands.CommandOnCooldown: (
                "Traditional command on cooldown",
                (commands.Cooldown(1, 15.0), 11.99),
            ),
            commands.MissingRequiredArgument: (
                "Traditional command missing required argument",
                (MockParameter("required_arg"),),
            ),
            commands.TooManyArguments: (
                "Traditional command too many arguments",
                ("Too many arguments provided",),
            ),
            commands.BotMissingPermissions: (
                "Bot missing permissions for traditional command",
                (["administrator", "manage_channels"],),
            ),
            commands.MemberNotFound: (
                "Traditional command member not found",
                ("NonExistentUser#1234",),
            ),
            commands.ExtensionNotLoaded: (
                "Extension not loaded error",
                ("fake.extension.name",),
            ),
        }

        if error_type in specific_mappings:
            description, args = specific_mappings[error_type]
            # Determine specific category for traditional command errors
            category = "Traditional Commands"
            if name in [
                "CheckFailure",
                "CheckAnyFailure",
                "PrivateMessageOnly",
                "NoPrivateMessage",
                "NotOwner",
                "NSFWChannelRequired",
            ]:
                category = "Check Failures"
            elif name in [
                "FlagError",
                "BadFlagArgument",
                "MissingRequiredFlag",
                "MissingFlagArgument",
                "TooManyFlags",
            ]:
                category = "Flag Errors"
            elif name.startswith("Extension") or name in [
                "NoEntryPointError",
                "CommandRegistrationError",
                "HybridCommandError",
            ]:
                category = "Extension Management"
            elif "NotFound" in name and name.endswith("NotFound"):
                category = "Entity Not Found"
            self.tests[name] = ErrorTestDefinition(
                error_type,
                args,
                {},
                description,
                category,
            )
        elif error_type == commands.MissingRole:
            self.tests[f"{name}_str"] = ErrorTestDefinition(
                error_type,
                ("RequiredRole",),
                {},
                "Traditional command missing role (by name)",
                "Check Failures",
            )
            self.tests[f"{name}_int"] = ErrorTestDefinition(
                error_type,
                (987654321012345678,),
                {},
                "Traditional command missing role (by ID)",
                "Check Failures",
            )
        elif hasattr(error_type, "__name__") and not error_type.__name__.startswith(
            "Extension",
        ):
            realistic_args = self._get_realistic_traditional_command_args(name)
            self.tests[name] = ErrorTestDefinition(
                error_type,
                realistic_args,
                {},
                f"Traditional command {name.lower().replace('error', ' error')}",
                category,
            )

    def _get_realistic_traditional_command_args(
        self,
        error_name: str,
    ) -> tuple[Any, ...]:
        """
        Get realistic arguments for traditional command errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the error type.
        """
        error_name_lower = error_name.lower()

        # Use mapping for cleaner logic
        if "notfound" in error_name_lower.replace("_", ""):
            notfound_mappings = {
                "channel": ("#invalid-channel",),
                "user": ("@InvalidUser#0000",),
                "member": ("@InvalidUser#0000",),
                "role": ("@InvalidRole",),
            }
            for keyword, args in notfound_mappings.items():
                if keyword in error_name_lower:
                    return args

        # Other mappings
        default_prefix = CONFIG.get_prefix()
        other_mappings = {
            ("command", "not"): (f"{default_prefix}nonexistent_command",),
            ("command",): (f"{default_prefix}mock error",),
            ("check",): ("Permission check failed",),
            ("conversion",): ("invalid_argument",),
        }

        return next(
            (
                args
                for keywords, args in other_mappings.items()
                if all(keyword in error_name_lower for keyword in keywords)
            ),
            (f"traditional_{error_name_lower}_example",),
        )

    def _add_discord_api_test(self, error_type: type[Exception]) -> None:
        """Add Discord API specific test cases."""
        name = error_type.__name__

        # Specific mappings for Discord API errors
        # Format: (description, args, kwargs)
        specific_mappings: dict[
            type[Exception],
            tuple[str, tuple[Any, ...], dict[str, Any]],
        ] = {
            discord.HTTPException: (
                "Discord API HTTP error response",
                (
                    MockObject(status=500, reason="Internal Server Error"),
                    "Mock HTTP Error",
                ),
                {},
            ),
            discord.RateLimited: ("Discord API rate limit hit", (15.5,), {}),
            discord.Forbidden: (
                "Discord API forbidden action",
                (MockObject(status=403, reason="Forbidden"), "Mock forbidden error"),
                {},
            ),
            discord.NotFound: (
                "Discord API resource not found",
                (MockObject(status=404, reason="Not Found"), "Mock not found error"),
                {},
            ),
            discord.DiscordServerError: (
                "Discord server error",
                (
                    MockObject(status=500, reason="Internal Server Error"),
                    "Mock server error",
                ),
                {},
            ),
            discord.ConnectionClosed: (
                "Discord connection closed",
                (MockObject(),),
                {"shard_id": None, "code": 4004},
            ),
            discord.GatewayNotFound: (
                "Discord gateway not found",
                (),
                {},
            ),
            discord.InvalidData: (
                "Discord API invalid data",
                ("Invalid JSON response",),
                {},
            ),
            discord.LoginFailure: (
                "Bot authentication failed",
                (),
                {},
            ),
            discord.PrivilegedIntentsRequired: (
                "Missing privileged intents",
                (None,),
                {},
            ),
            discord.InteractionResponded: (
                "Interaction already responded",
                (MockObject(),),
                {},
            ),
            discord.MissingApplicationID: (
                "Missing application ID",
                (),
                {},
            ),
        }

        if error_type in specific_mappings:
            description, args, kwargs = specific_mappings[error_type]
            # Determine specific category for Discord API errors
            category = "Discord API"
            if name in [
                "ConnectionClosed",
                "GatewayNotFound",
                "InvalidData",
                "LoginFailure",
                "PrivilegedIntentsRequired",
                "InteractionResponded",
                "MissingApplicationID",
            ]:
                category = "Client Connection"
            self.tests[name] = ErrorTestDefinition(
                error_type,
                args,
                kwargs,
                description,
                category,
            )
        elif hasattr(error_type, "__name__"):
            realistic_args = self._get_realistic_discord_args(name)
            # Determine specific category for Discord API errors
            category = "Discord API"
            if name in [
                "ConnectionClosed",
                "GatewayNotFound",
                "InvalidData",
                "LoginFailure",
                "PrivilegedIntentsRequired",
                "InteractionResponded",
                "MissingApplicationID",
            ]:
                category = "Client Connection"
            self.tests[name] = ErrorTestDefinition(
                error_type,
                realistic_args,
                {},
                f"Discord API {name.lower().replace('error', ' error')}",
                category,
            )

    def _get_realistic_discord_args(self, error_name: str) -> tuple[Any, ...]:
        """
        Get realistic arguments for Discord API errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the error type.
        """
        error_name_lower = error_name.lower()

        # Use mapping for cleaner logic
        arg_mappings = {
            ("notfound", "channel"): ("#invalid-channel",),
            ("notfound", "user"): ("@InvalidUser#0000",),
            ("notfound", "member"): ("@InvalidUser#0000",),
            ("notfound", "role"): ("@InvalidRole",),
            ("notfound", "webhook"): ("https://discord.com/api/webhooks/invalid",),
            ("forbidden",): ("403 Forbidden",),
            ("invalid",): ("Invalid parameter",),
            ("http",): ("HTTP 500 Error",),
            ("timeout",): ("Request timeout",),
        }

        return next(
            (
                args
                for keywords, args in arg_mappings.items()
                if all(keyword in error_name_lower for keyword in keywords)
            ),
            (f"discord_{error_name_lower}_example",),
        )

    def _add_httpx_test(self, error_type: type[Exception]) -> None:
        """Add HTTPX error test cases."""
        name = error_type.__name__

        # Specific mappings for HTTPX errors
        specific_mappings = {
            httpx.HTTPError: ("HTTP request error", ("Mock HTTP error",)),
            httpx.HTTPStatusError: ("HTTP status error", ("Mock HTTP status error",)),
            httpx.TimeoutException: ("HTTP timeout", ("Mock timeout",)),
            httpx.ConnectError: ("HTTP connection error", ("Mock connection error",)),
            httpx.ReadTimeout: ("HTTP read timeout", ("Mock read timeout",)),
            httpx.WriteTimeout: ("HTTP write timeout", ("Mock write timeout",)),
            httpx.PoolTimeout: ("HTTP pool timeout", ("Mock pool timeout",)),
            httpx.RequestError: ("HTTP request error", ("Mock request error",)),
        }

        if error_type in specific_mappings:
            description, args = specific_mappings[error_type]
            self.tests[name] = ErrorTestDefinition(
                error_type,
                args,
                {},
                description,
                "HTTPX Errors",
            )
        elif hasattr(error_type, "__name__"):
            # Generic HTTPX error
            realistic_args = self._get_realistic_httpx_args(name)
            self.tests[name] = ErrorTestDefinition(
                error_type,
                realistic_args,
                {},
                f"HTTPX {name.lower().replace('error', ' error')}",
                "HTTPX Errors",
            )

    def _add_builtin_test(self, error_type: type[Exception]) -> None:
        """Add Python built-in error test cases for unhandled error testing."""
        name = error_type.__name__
        realistic_args = self._get_realistic_builtin_args(name)
        self.tests[name] = ErrorTestDefinition(
            error_type,
            realistic_args,
            {},
            f"Python built-in {name.lower().replace('error', ' error')} (should be unhandled)",
            "Unhandled",
        )

    def _get_realistic_httpx_args(self, error_name: str) -> tuple[Any, ...]:
        """
        Get realistic arguments for HTTPX errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the HTTPX error type.
        """
        # Most HTTPX errors need minimal args, they inherit from Exception
        return (f"Mock HTTPX {error_name.lower().replace('error', ' error')}",)

    def _get_realistic_builtin_args(self, error_name: str) -> tuple[Any, ...]:
        """
        Get realistic arguments for Python built-in errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the error type.
        """
        error_name_lower = error_name.lower()

        # Use mapping for cleaner logic
        arg_mappings = {
            "valueerror": ("invalid literal for int() with base 10: 'abc'",),
            "typeerror": ("'NoneType' object is not iterable",),
            "keyerror": ("'missing_key'",),
            "indexerror": ("list index out of range",),
            "attributeerror": ("'str' object has no attribute 'missing_attr'",),
            "filenotfounderror": (
                "[Errno 2] No such file or directory: 'missing_file.txt'",
            ),
            "permissionerror": ("[Errno 13] Permission denied: '/protected/file.txt'",),
            "zerodivisionerror": ("division by zero",),
            "assertionerror": ("Test assertion failed",),
        }

        return arg_mappings.get(
            error_name_lower,
            (f"python_{error_name_lower}_example",),
        )

    def _add_custom_test(self, error_type: type[Exception]) -> None:
        """Add custom error test cases for tux module errors."""
        name = error_type.__name__
        realistic_args = self._get_realistic_custom_args(name)
        self.tests[name] = ErrorTestDefinition(
            error_type,
            realistic_args,
            {},
            f"Custom tux {name.lower().replace('error', ' error')}",
            "Custom",
        )

    def _get_realistic_custom_args(self, error_name: str) -> tuple[Any, ...]:
        """
        Get realistic arguments for custom tux errors.

        Returns
        -------
        tuple[Any, ...]
            Arguments appropriate for the error type.
        """
        error_name_lower = error_name.lower()

        # Use mapping for cleaner logic
        arg_mappings = {
            ("config",): ("Configuration error",),
            ("database",): ("Database connection failed",),
            ("permission",): ("Insufficient permissions",),
            ("validation",): ("Input validation failed",),
        }

        return next(
            (
                args
                for keywords, args in arg_mappings.items()
                if all(keyword in error_name_lower for keyword in keywords)
            ),
            (f"custom_{error_name_lower}_example",),
        )

    def get_test_names(self) -> list[str]:
        """
        Get all test names.

        Returns
        -------
        list[str]
            List of all registered test names.
        """
        return list(self.tests.keys())

    def get_test_names_by_category(self) -> dict[str, list[str]]:
        """
        Get test names grouped by category.

        Returns
        -------
        dict[str, list[str]]
            Dictionary mapping category names to lists of test names.
        """
        categories: dict[str, list[str]] = {}
        for name, test_def in self.tests.items():
            category = test_def.category
            categories.setdefault(category, []).append(name)
        return categories

    def get_test(self, name: str) -> ErrorTestDefinition | None:
        """
        Get a specific test by name.

        Returns
        -------
        ErrorTestDefinition | None
            The test definition if found, None otherwise.
        """
        return self.tests.get(name)


class Mock(BaseCog):
    """Mock plugin for Tux Bot."""

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the Mock cog.

        Parameters
        ----------
        bot : Tux
            The bot instance.
        """
        super().__init__(bot)
        self.error_registry = ErrorTestRegistry()

    async def _create_error_info_embed(
        self,
        test_name: str,
        test_def: ErrorTestDefinition,
        ctx: commands.Context[Tux],
    ) -> discord.Embed:
        """
        Create an informative embed showing error details and expected handler behavior.

        Returns
        -------
        discord.Embed
            The informational embed.
        """
        config = test_def.get_config()

        # Create main embed with cleaner title and description
        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.INFO,
            bot=self.bot,
            title=f"🧪 Testing: `{test_def.error_class.__name__}`",
            description=f"**{test_def.description}**",
            user_name=ctx.author.display_name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        # Enhanced status line with category included - user-friendly format
        if config:
            sentry_status = "✅ Enabled" if config["send_to_sentry"] else "❌ Disabled"
            log_level = config["log_level"]
            log_icon = {
                "ERROR": "🔴",
                "WARNING": "🟡",
                "INFO": "🔵",
                "DEBUG": "⚪",
            }.get(log_level, "🔵")
            embed_type = (
                "📁 Custom" if config["has_detail_extractor"] else "📁 Standard"
            )
            category_icon = {
                "Application Commands": "🔵",
                "Traditional Commands": "🔵",
                "Check Failures": "🔒",
                "Flag Errors": "🏴",
                "Extension Management": "📦",
                "Entity Not Found": "🔍",
                "Client Connection": "🔌",
                "Discord API": "🤖",
                "Custom Errors": "🗒️",
                "HTTPX Errors": "🌐",
                "Base Exceptions": "⚠️",
            }.get(test_def.category, "🔵")

            status_line = f"**Sentry:** {sentry_status} • **Log Level:** {log_icon} {log_level} • **Embed Type:** {embed_type} • **Category:** {category_icon} {test_def.category}"

            embed.add_field(
                name="⚙️ Handler Configuration",
                value=status_line,
                inline=False,
            )
        else:
            category_icon = "🔵"
            status_line = f"**Sentry:** ❌ Disabled • **Log Level:** 📁 ERROR • **Embed Type:** 📁 Standard • **Category:** {category_icon} {test_def.category}"

            embed.add_field(
                name="⚠️ Unhandled Error",
                value=status_line,
                inline=False,
            )

        # Use single-column layout for better readability
        if config:
            # Show the user message format (truncated for readability)
            message_preview = config["message_format"]
            if len(message_preview) > 100:
                message_preview = f"{message_preview[:97]}..."

            embed.add_field(
                name="💬 User Message",
                value=f"```\n{message_preview}\n```",
                inline=False,
            )
        else:
            embed.add_field(
                name="💬 User Message",
                value="```\nUnhandled error logged to console\n```",
                inline=False,
            )

        # Technical details - show real source
        args_preview = str(test_def.args)
        if len(args_preview) > 60:
            args_preview = f"{args_preview[:57]}..."

        embed.add_field(
            name="🔧 Technical Info",
            value=f"**Module:** `{test_def.error_class.__module__}`\n**Args:** `{args_preview}`",
            inline=False,
        )

        # Context-aware "What's Next" section
        if config:
            severity = config["log_level"]
            if severity == "ERROR":
                next_msg = "📁 **High Severity** - This error will be raised in **1 second**:\n• Error response sent to channel\n• Console logging\n• Sentry event tracked"
            elif config["send_to_sentry"]:
                next_msg = "📁 **Monitored Error** - Raising in **1 second**:\n• User-friendly response\n• Console logging\n• Sentry tracking enabled"
            else:
                next_msg = "📁 **Standard Error** - Raising in **1 second**:\n• User response in channel\n• Console logging only"
        else:
            next_msg = "📁 **Unhandled Path** - Raising in **1 second**:\n• No user response (unexpected error)\n• Full stack trace logged\n• May trigger fallback handling"

        embed.add_field(
            name="🚀 What Happens Next",
            value=next_msg,
            inline=False,
        )

        return embed

    async def _send_test_summary(self, ctx: commands.Context[Tux]) -> None:
        """Send a summary of available error tests."""
        categories = self.error_registry.get_test_names_by_category()

        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.INFO,
            bot=self.bot,
            title="🧪 Available Error Tests",
            description=f"There are **{len(self.error_registry.get_test_names())}** error tests available across **{len(categories)}** categories.",
            user_name=ctx.author.display_name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        for category, tests in categories.items():
            test_list = ", ".join(f"`{test}`" for test in sorted(tests)[:5])
            if len(tests) > 5:
                test_list += f" ... and {len(tests) - 5} more"

            embed.add_field(
                name=f"📁 {category} ({len(tests)})",
                value=test_list or "None",
                inline=False,
            )

        # Get the active prefix for this guild
        prefix = (
            await self.bot.prefix_manager.get_prefix(ctx.guild.id)
            if ctx.guild and self.bot.prefix_manager
            else "$"
        )

        embed.add_field(
            name="📁 Usage",
            value=f"Use `/mock error <error_name>` or `{prefix}mock error <error_name>` with autocomplete to test specific errors.",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.hybrid_group(
        name="mock",
        description="Commands to mock bot behaviors for testing.",
    )
    @requires_command_permission()
    async def mock(self, ctx: commands.Context[Tux]) -> None:
        """
        Command group for mocking various bot behaviors.

        Requires System Administrator permissions (Level 8).
        """
        if ctx.invoked_subcommand is None:
            await self._send_test_summary(ctx)

    async def error_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete function for error names based on the selected category.

        Returns
        -------
        list[app_commands.Choice[str]]
            List of autocomplete choices (max 25).
        """
        # Get the category from the current interaction
        category = None
        if interaction.namespace:
            category = getattr(interaction.namespace, "category", None)

        if not category:
            # If no category selected yet, show popular/common errors
            common_errors = [
                "ValueError",
                "RuntimeError",
                "App_MissingRole_str",
                "Cmd_MissingPermissions",
                "Forbidden",
                "App_CommandOnCooldown",
                "Cmd_CommandOnCooldown",
            ]
            choices = [
                app_commands.Choice(name=error_name, value=error_name)
                for error_name in common_errors
                if current.lower() in error_name.lower()
            ]
        else:
            # Filter errors by the selected category
            categories = self.error_registry.get_test_names_by_category()

            if category == "All":
                # Show all errors if "All" is selected
                available_errors = self.error_registry.get_test_names()
            else:
                # Show only errors from the selected category
                available_errors = categories.get(category, [])

            # Filter based on current input and limit to 25
            filtered_errors = [
                error_name
                for error_name in available_errors
                if current.lower() in error_name.lower()
            ]

            choices = [
                app_commands.Choice(
                    name=(
                        f"{error_name} [{self.error_registry.tests[error_name].category}]"
                        if category == "All" and error_name in self.error_registry.tests
                        else error_name
                    ),
                    value=error_name,
                )
                for error_name in filtered_errors
            ]

        # Sort and limit choices
        choices.sort(key=lambda x: x.name)
        return choices[:25]

    @mock.command(
        name="error",
        description="Raise a specified error for testing error handling.",
    )
    @app_commands.describe(
        category="Select the category of error to test",
        error_name="Choose the specific error from the selected category",
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="All Categories", value="All"),
            app_commands.Choice(
                name="Application Commands",
                value="Application Commands",
            ),
            app_commands.Choice(
                name="Traditional Commands",
                value="Traditional Commands",
            ),
            app_commands.Choice(name="Check Failures", value="Check Failures"),
            app_commands.Choice(name="Flag Errors", value="Flag Errors"),
            app_commands.Choice(
                name="Extension Management",
                value="Extension Management",
            ),
            app_commands.Choice(name="Entity Not Found", value="Entity Not Found"),
            app_commands.Choice(name="Client Connection", value="Client Connection"),
            app_commands.Choice(name="Discord API", value="Discord API"),
            app_commands.Choice(name="Custom Errors", value="Custom Errors"),
            app_commands.Choice(name="HTTPX Errors", value="HTTPX Errors"),
            app_commands.Choice(name="Base Exceptions", value="Base Exceptions"),
        ],
    )
    @app_commands.autocomplete(error_name=error_name_autocomplete)
    @requires_command_permission()
    async def mock_error(
        self,
        ctx: commands.Context[Tux],
        category: str,
        error_name: str | None = None,
    ) -> None:
        """
        Raise a specified error to test the global error handler.

        This command shows detailed information about how the error will be handled,
        then raises the error to demonstrate the actual behavior.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command invocation context.
        category : str
            The category of error to test (required for slash commands).
        error_name : str, optional
            The specific error name to test. If not provided, shows available errors in the category.

        Notes
        -----
        This command intentionally raises various exceptions based on the input.
        These exceptions will propagate up to the global ErrorHandler cog.
        Requires System Administrator permissions (Level 8).
        """
        # If no specific error name provided, show available errors in the category
        if not error_name:
            await self._send_category_summary(ctx, category)
            return

        # Handle "All" category - need to find the error across all categories
        if category != "All":
            # Find the error in the specific category
            category_tests = self.error_registry.get_test_names_by_category().get(
                category,
                [],
            )
            if error_name not in category_tests:
                await self._send_error_not_in_category(ctx, error_name, category)
                return

        test_def = self.error_registry.get_test(error_name)
        if not test_def:
            await self._send_error_not_found(ctx, error_name, category)
            return

        # Create and send the info embed first
        info_embed = await self._create_error_info_embed(error_name, test_def, ctx)
        await ctx.send(embed=info_embed)

        # Add a small delay for dramatic effect and to ensure the info embed is sent first
        await asyncio.sleep(1.0)

        # Log the intentional error raising
        logger.debug(f"Mock error test: {error_name} by {ctx.author}")

        # Now raise the actual error for testing
        error = test_def.create_error()
        raise error

    async def _send_category_summary(
        self,
        ctx: commands.Context[Tux],
        category: str,
    ) -> None:
        """Send a summary of available errors in a specific category."""
        categories = self.error_registry.get_test_names_by_category()

        if category == "All":
            await self._send_test_summary(ctx)
            return

        if category not in categories:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedCreator.ERROR,
                bot=self.bot,
                title="• Invalid Category",
                description=f"Category `{category}` not found.",
                user_name=ctx.author.display_name,
                user_display_avatar=ctx.author.display_avatar.url,
            )
            await ctx.send(embed=embed)
            return

        tests = categories[category]
        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.INFO,
            bot=self.bot,
            title=f"📁 {category} Error Tests",
            description=f"Available error tests in the **{category}** category ({len(tests)} total):",
            user_name=ctx.author.display_name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        # Group tests into chunks for better display
        test_chunks = [tests[i : i + 10] for i in range(0, len(tests), 10)]

        for i, chunk in enumerate(test_chunks):
            field_name = (
                f"📁 Tests {i * 10 + 1}-{min((i + 1) * 10, len(tests))}"
                if len(test_chunks) > 1
                else "📁 Available Tests"
            )
            test_list = "\n".join(f"• `{test}`" for test in sorted(chunk))
            embed.add_field(name=field_name, value=test_list, inline=False)

        embed.add_field(
            name="📁 Usage",
            value=f"Use `/mock error category:{category} error_name:<test_name>` to test a specific error.",
            inline=False,
        )

        await ctx.send(embed=embed)

    async def _send_error_not_in_category(
        self,
        ctx: commands.Context[Tux],
        error_name: str,
        category: str,
    ) -> None:
        """Send an error message when the error is not found in the specified category."""
        categories = self.error_registry.get_test_names_by_category()
        category_tests = categories.get(category, [])

        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.ERROR,
            bot=self.bot,
            title="• Error Not Found in Category",
            description=f"Error `{error_name}` not found in category `{category}`.",
            user_name=ctx.author.display_name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        test_list = "None"
        if category_tests:
            # Show some available tests in this category
            test_list = ", ".join(f"`{test}`" for test in sorted(category_tests)[:5])
            if len(category_tests) > 5:
                test_list = f"{test_list} ... and {len(category_tests) - 5} more"

        embed.add_field(
            name=f"📁 Available in {category}",
            value=test_list,
            inline=False,
        )

        # Check if the error exists in other categories
        for cat_name, cat_tests in categories.items():
            if error_name in cat_tests and cat_name != category:
                embed.add_field(
                    name="📁 Found in Different Category",
                    value=f"`{error_name}` is available in the **{cat_name}** category.",
                    inline=False,
                )
                break

        await ctx.send(embed=embed)

    async def _send_error_not_found(
        self,
        ctx: commands.Context[Tux],
        error_name: str,
        category: str,
    ) -> None:
        """Send an error message when the error is not found at all."""
        available_categories = self.error_registry.get_test_names_by_category()
        embed = EmbedCreator.create_embed(
            embed_type=EmbedCreator.ERROR,
            bot=self.bot,
            title="• Error Test Not Found",
            description=f"Error type `{error_name}` not found in category `{category}` or any other category.",
            user_name=ctx.author.display_name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        # Show available categories
        for cat_name, tests in list(available_categories.items())[
            :3
        ]:  # Show first 3 categories
            test_list = ", ".join(f"`{test}`" for test in sorted(tests)[:3])
            if len(tests) > 3:
                test_list = f"{test_list} ... ({len(tests)} total)"
            embed.add_field(name=f"📁 {cat_name}", value=test_list, inline=False)

        # Get the active prefix for this guild
        prefix = (
            await self.bot.prefix_manager.get_prefix(ctx.guild.id)
            if ctx.guild and self.bot.prefix_manager
            else "$"
        )

        embed.add_field(
            name="📁 Tip",
            value=f"Use the category dropdown first, then specify the error name, or run `{prefix}mock` to see all available tests.",
            inline=False,
        )

        await ctx.send(embed=embed)

    # Keep the old autocomplete version for prefix commands
    async def error_type_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete function for error types with category information.

        Returns
        -------
        list[app_commands.Choice[str]]
            List of autocomplete choices with category prefix (max 25).
        """
        choices = [
            app_commands.Choice(name=f"[{test_def.category}] {name}", value=name)
            for name, test_def in self.error_registry.tests.items()
            if current.lower() in name.lower()
        ]

        # Sort by category, then by name, and limit to 25
        choices.sort(key=lambda x: x.name)
        return choices[:25]

    # Add a separate command for the old-style interface for prefix commands
    @mock.command(
        name="test",
        description="Test a specific error by name (with autocomplete).",
    )
    @app_commands.autocomplete(error_type=error_type_autocomplete)
    @requires_command_permission()
    async def mock_test(self, ctx: commands.Context[Tux], *, error_type: str) -> None:
        """
        Alternative error testing command with autocomplete support.

        This provides the old interface for those who prefer typing error names directly.
        """
        test_def = self.error_registry.get_test(error_type)
        if not test_def:
            await self._send_error_not_found(ctx, error_type, "All")
            return

        # Create and send the info embed first
        info_embed = await self._create_error_info_embed(error_type, test_def, ctx)
        await ctx.send(embed=info_embed)

        # Add a small delay for dramatic effect
        await asyncio.sleep(1.0)

        # Log the intentional error raising
        logger.debug(f"Mock error test: {error_type} by {ctx.author}")

        # Now raise the actual error for testing
        error = test_def.create_error()
        raise error


async def setup(bot: Tux) -> None:
    """Cog setup for event handler.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(Mock(bot))
