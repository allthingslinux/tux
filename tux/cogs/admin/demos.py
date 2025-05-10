"""
Discord.py Demo Examples for Tux Bot

This file serves as a comprehensive showcase of various discord.py features,
implemented within the context of the Tux bot project. It demonstrates best practices
such as cog organization, command types (prefix, slash, hybrid), error handling,
checks, database interaction, and UI elements like embeds.

All demo commands are intentionally grouped under the `demo` command group
for clarity and organization.

Ref:
- Cogs: https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html
"""

from datetime import UTC, datetime
from typing import Literal, cast

import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

# Project-specific imports
from tux.bot import Tux  # The main bot class
from tux.database.controllers import DatabaseController  # For database interaction examples
from tux.ui.embeds import EmbedCreator, EmbedType  # Standardized embed creation utility
from tux.utils import checks  # Custom checks for permissions/roles
from tux.utils.constants import CONST  # Project-wide constants (e.g., embed colors, delete after)
from tux.utils.functions import datetime_to_unix  # Utility to format datetime objects

# Demo choices for autocomplete in slash commands
# This list is used later in an `app_commands.command` example.
FRUIT_CHOICES = ["Apples", "Bananas", "Cherries", "Kiwi", "Mango", "Orange", "Pineapple"]


# Cog class definition
# Inherits from commands.Cog to be recognized by the bot's cog loader.
# Setting `name` provides a user-friendly name for help commands, etc.
class DemoCog(commands.Cog, name="Demo Examples"):
    """
    Demo commands showcasing discord.py features.

    This cog encapsulates all demonstration commands, adhering to the best practice
    of organizing bot functionality into logical modules (Cogs). It provides examples
    of different command types, decorators, error handling, and interaction with
    other parts of the Tux bot framework (database, UI).

    Ref:
    - commands.Cog: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Cog
    """

    def __init__(self, bot: Tux) -> None:
        """
        Initialize the DemoCog.

        This constructor is called when the cog is loaded by the bot.
        It stores the bot instance for later use and initializes dependencies.

        Parameters
        ----------
        bot : Tux
            The bot instance, passed automatically by the cog loader.
            Provides access to bot properties (like latency) and methods.

        Ref:
        - Cog `__init__`: https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#quick-example
        """
        self.bot = bot

        # Initialize database controller for DB demos
        # Best practice: Encapsulate database logic within controller classes.
        # In a real application, this might involve dependency injection.
        # Using a placeholder class `DatabaseController()` for demonstration.
        self._db = DatabaseController()  # type: ignore # Placeholder for actual init

        # Generate usage strings for commands (Example of project-specific utility integration)
        # This demonstrates dynamically generating help/usage information,
        # potentially using custom flag parsing logic defined elsewhere in the project.
        # The `hasattr` check ensures this runs only if the command group exists,
        # preventing errors during initialization if the command definition changes.
        try:
            from tux.utils.flags import generate_usage

            if hasattr(self, "demo_example_group") and hasattr(self.demo_example_group, "usage"):
                self.demo_example_group.usage = generate_usage(self.demo_example_group)
        except ImportError:
            logger.warning("Could not import generate_usage from tux.utils.flags.")
        except Exception as e:
            logger.error(f"Error generating usage string for demo_example_group: {e}")

    # Cog-specific check
    # This check applies to *all* commands within this cog.
    # Adding type: ignore to suppress pyright override warning while keeping specific hint.
    def cog_check(self, ctx: commands.Context[Tux]) -> bool:  # type: ignore
        """
        A local check that applies to all commands in this cog.

        Ensures that commands in this cog can only be used within a server (guild context),
        not in direct messages. This is a common requirement for commands that rely on
        guild information (members, roles, channels).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context for the command invocation.

        Returns
        -------
        bool
            True if the check passes (command is in a guild), False otherwise.

        Ref:
        - `cog_check`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Cog.cog_check
        - `ctx.guild`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context.guild
        """
        # Only allow commands in this cog to be used in a guild
        # Cast ctx.bot to Tux if needed inside the check
        # bot: Tux = cast(Tux, ctx.bot)
        return ctx.guild is not None

    # Cog-specific error handler
    # Catches errors raised by commands within this cog that aren't handled locally.
    # Adding type: ignore to suppress pyright override warning while keeping specific hint.
    async def cog_command_error(self, ctx: commands.Context[Tux], error: Exception) -> None:  # type: ignore
        """
        A local error handler for all commands in this cog.

        Handles specific errors like `CommandOnCooldown` locally within the cog.
        For unhandled errors, it logs them and informs the user. This demonstrates
        layered error handling (global handler + cog-level handler + command-level try/except).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context where the command error occurred.
        error : Exception
            The error that was raised during command invocation or processing.

        Ref:
        - `cog_command_error`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Cog.cog_command_error
        - `commands.CommandInvokeError`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.CommandInvokeError
        - `commands.CommandOnCooldown`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.CommandOnCooldown
        """
        # Best practice: Unwrap CommandInvokeError to get the root cause.
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        # Handle cooldown errors specifically
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(int(error.retry_after), 60)
            # Provide user-friendly feedback about the cooldown.
            # `delete_after` helps keep the channel clean.
            await ctx.send(f"This command is on cooldown. Try again in {minutes}m {seconds}s.", delete_after=10)
            return

        # Log unexpected errors for debugging.
        # Using loguru (or standard logging) is crucial for monitoring.
        command_name = ctx.command.qualified_name if ctx.command else "Unknown Command"
        logger.error(f"Error in command '{command_name}': {error}", exc_info=True)  # Add exc_info for traceback

        # Inform the user about the unexpected error. Avoid exposing sensitive details.
        await ctx.send(
            f"An unexpected error occurred while running `{command_name}`. The developers have been notified.",
        )

    # ==================================================
    # MAIN DEMO COMMAND GROUP
    # ==================================================

    # Defines a command group 'demo'.
    # `invoke_without_command=True` allows the group itself to be called as a command.
    # If False, calling `demo` without a subcommand would raise an error.
    @commands.group(invoke_without_command=True)
    async def demo(self, ctx: commands.Context[Tux]) -> None:
        """
        Discord.py demo examples main command group.

        Acts as the entry point for all demo commands. When invoked without a subcommand,
        it displays an overview embed listing the available demo categories and examples.
        This uses the standard `discord.Embed` for a simple informational display.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked. Provided automatically.

        Ref:
        - `commands.group`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.group
        - `invoke_without_command`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Group.invoke_without_command
        - `discord.Embed`: https://discordpy.readthedocs.io/en/stable/api.html#discord.Embed
        """
        # Using a standard discord.Embed here for demonstration.
        # Other commands might use the project's `EmbedCreator` for consistency.
        embed = discord.Embed(
            title="Discord.py Demo Examples",
            description=(
                "Welcome to the Tux bot demo command suite!\n\n"
                "Explore various discord.py features organized into categories.\n"
                "Use `demo <subcommand>` to see specific examples.\n\n"
                "**Quick Examples:**\n"
                "`demo hello` - A simple greeting.\n"
                "`demo echo <your text>` - Repeats your message.\n"
                "`demo example sub1` - Executes a nested subcommand.\n"
                "`demo db stats` - Shows simulated database statistics.\n"
                "`demo demo_ping` - Checks bot latency (Hybrid Command)."
            ),
            color=discord.Color.blue(),  # Using a basic color. CONST might be used elsewhere.
        )

        # Add fields outlining the different categories of demo commands.
        embed.add_field(
            name="📚 Basic Commands",
            value="`demo basic` - Traditional prefix-based command examples.",
            inline=False,
        )
        embed.add_field(
            name="<:slash_command:123456789012345678> Application Commands",  # Example: Replace with actual emoji ID if available
            value="`demo slash` - Slash command (`/`) examples.",
            inline=False,
        )
        embed.add_field(
            name="🔄 Hybrid Commands",
            value="`demo hybrid` - Commands usable via prefix OR slash.",
            inline=False,
        )
        embed.add_field(
            name="🗄️ Database Examples",
            value="`demo db` - Demonstrations of database interactions.",
            inline=False,
        )
        embed.add_field(
            name="✨ Other Features",
            value=(
                "Explore features like event listeners and background tasks (code-level)."
            ),  # Note: Events/Tasks often don't have direct user commands.
            inline=False,
        )
        # Corrected multi-line string formatting for value
        embed.add_field(
            name="🚀 Direct Try-Outs",
            value=(
                "`demo hello`\n"
                "`demo echo <text>`\n"
                "`demo cooldown`\n"
                "`demo demo_ping`\n"
                "`demo userinfo [user]`\n"
                "`demo calc add 5 3`"
            ),
            inline=False,
        )

        embed.set_footer(text="All examples are nested under the 'demo' command group.")

        await ctx.send(embed=embed)

    # ==================================================
    # CATEGORY INFORMATION COMMANDS
    # ==================================================
    # These commands provide help/info about the subcategories of demos.

    @demo.command(name="basic")
    async def demo_basic(self, ctx: commands.Context[Tux]) -> None:
        """
        Provides information about traditional prefix command examples.

        Uses the project's `EmbedCreator` for consistent embed styling.
        Lists examples available under the `demo` group that demonstrate
        simple commands, groups, and checks using the `commands.ext` framework.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        """
        # Using the project's EmbedCreator for consistent styling and structure.
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,  # Predefined style for informational messages
            title="Basic Commands Examples",
            # Corrected multi-line string formatting for description
            description=(
                "These examples showcase traditional prefix commands using `discord.ext.commands`.\n\n"
                "**Usage:** `demo <command> [arguments]` (e.g., `demo echo Hello`)"
            ),
        )

        embed.add_field(
            name="Simple Commands",
            # Corrected multi-line string formatting for value
            value=("`demo hello` - Simple greeting.\n`demo echo <text>` - Echoes text back."),
            inline=False,
        )
        embed.add_field(
            name="Command Groups",
            # Corrected multi-line string formatting for value
            value=(
                "`demo example` - Base group command.\n"
                "`demo example sub1 [message]` - Subcommand with optional argument.\n"
                "`demo example sub2 <user>` - Subcommand requiring a member."
            ),
            inline=False,
        )
        embed.add_field(
            name="Checks & Cooldowns",
            # Corrected multi-line string formatting for value
            value=(
                "`demo owner` - Usable only by the bot owner (`@commands.is_owner()`).\n"
                "`demo permission` - Requires 'Manage Messages' permission (`@commands.has_permissions`).\n"
                "`demo cooldown` - Rate-limited command (`@commands.cooldown`)."
            ),
            inline=False,
        )

        # Using a constant for delete delay promotes maintainability.
        await ctx.send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)

    @demo.command(name="slash")
    async def demo_slash(self, ctx: commands.Context[Tux]) -> None:
        """
        Provides information about Application (Slash) command examples.

        Explains slash command usage and lists examples demonstrating features like
        choices, autocomplete, and command groups using the `discord.app_commands` module.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.
        """
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="Slash Commands Examples",
            # Corrected multi-line string formatting for description
            description=(
                "These examples showcase Application Commands (Slash Commands) using `discord.app_commands`.\n\n"
                "**Usage:** Type `/` in Discord and select the command from the list."
            ),
        )

        embed.add_field(name="Basic Slash Command", value="`/greet <user>` - Simple greeting.", inline=False)
        embed.add_field(
            name="Parameters with Choices",
            value="`/choose_fruit <fruit> <rating>` - Uses predefined choices (`@app_commands.choices`).",
            inline=False,
        )
        embed.add_field(
            name="Parameters with Autocomplete",
            value="`/search_fruit <query>` - Provides dynamic suggestions as you type (`@app_commands.autocomplete`).",  # Note: Autocomplete example needs to be added
            inline=False,
        )
        embed.add_field(
            name="Slash Command Groups",
            value="`/fruit info <name>` - Organizes commands under a group (`app_commands.Group`).",
            inline=False,
        )

        await ctx.send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)

    @demo.command(name="hybrid")
    async def demo_hybrid(self, ctx: commands.Context[Tux]) -> None:
        """
        Provides information about Hybrid Command examples.

        Explains that hybrid commands work as both prefix and slash commands.
        Lists examples demonstrating basic hybrid commands and hybrid groups.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is invoked.

        Ref:
        - Hybrid Commands: https://discordpy.readthedocs.io/en/stable/ext/commands/hybrid.html
        """
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="Hybrid Commands Examples",
            # Corrected multi-line string formatting for description
            description=(
                "Hybrid commands offer flexibility, working as both traditional prefix commands\n"
                "and modern slash commands using `@commands.hybrid_command` or `@commands.hybrid_group`.\n\n"
                "**Usage:**\n"
                "- Prefix: `demo <command> [args]` (e.g., `demo demo_ping`)\n"
                "- Slash: `/<command> [args]` (e.g., `/demo_ping`)"
            ),
        )

        embed.add_field(
            name="Available Hybrid Commands",
            # Corrected multi-line string formatting for value
            value=(
                "`demo demo_ping` / `/demo_ping` - Checks bot latency.\n"
                "`demo userinfo [user]` / `/userinfo [user]` - Shows user details (Note: needs conversion to hybrid).\n"  # Assuming userinfo is or will be hybrid
                "`demo calc <subcommand>` / `/calc <subcommand>` - Calculator functions (Group)."
            ),
            inline=False,
        )
        embed.add_field(
            name="Calculator Group Example",
            # Corrected multi-line string formatting for value
            value=(
                "`demo calc add <num1> <num2>` / `/calc add num1 num2`\n"
                "`demo calc subtract ...` / `/calc subtract ...`\n"
                "`demo calc multiply ...` / `/calc multiply ...`\n"
                "`demo calc divide ...` / `/calc divide ...`"
            ),
            inline=False,
        )

        await ctx.send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)

    # ==================================================
    # BASIC COMMAND EXAMPLES (using discord.ext.commands)
    # ==================================================

    @demo.command(name="hello")
    async def demo_hello(self, ctx: commands.Context[Tux]) -> None:
        """
        A minimal prefix command example. Responds with a simple greeting.

        Demonstrates the basic structure of a command function decorated with
        `@<group_name>.command()`.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object, automatically passed, contains invocation details.
        """
        await ctx.send(f"Hello there, {ctx.author.mention}!")

    @demo.command(name="echo")
    async def demo_echo(self, ctx: commands.Context[Tux], *, text: str) -> None:
        """
        Echoes the provided text back. Demonstrates argument handling.

        The `*` in `*, text: str` indicates that `text` is a "keyword-only argument"
        that consumes the rest of the input message after the command name.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        text : str
            The text provided by the user after the command name.

        Ref:
        - Argument Converters: https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#parameters
        - Keyword-Only Arguments: https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#keyword-only-arguments
        """
        await ctx.send(f"You wanted me to say: {text}")

    @demo.command(name="owner")
    @commands.is_owner()  # Decorator check: Only the bot owner(s) can run this.
    async def demo_owner(self, ctx: commands.Context[Tux]) -> None:
        """
        Command restricted to the bot owner(s) using the `is_owner` check.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.

        Ref:
        - `commands.is_owner`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.is_owner
        - Checks: https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#checks
        """
        await ctx.send(f"Ah, greetings, esteemed owner {ctx.author.mention}!")

    @demo.command(name="permission")
    # Decorator check: Requires the invoking user to have 'Manage Messages' permission.
    @commands.has_permissions(manage_messages=True)
    async def demo_permission(self, ctx: commands.Context[Tux]) -> None:
        """
        Command restricted by user permissions using `has_permissions`.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.

        Ref:
        - `commands.has_permissions`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.has_permissions
        """
        await ctx.send(f"Confirmed, {ctx.author.mention}, you have the 'Manage Messages' permission in this channel!")

    @demo.command(name="cooldown")
    # Decorator: Applies a cooldown (rate limit).
    # 1 use per 30 seconds, per user (`BucketType.user`).
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def demo_cooldown(self, ctx: commands.Context[Tux]) -> None:
        """
        Command with a user-specific cooldown using the `cooldown` decorator.

        If invoked while on cooldown, it raises `commands.CommandOnCooldown`,
        which is handled by the `cog_command_error` handler in this cog.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.

        Ref:
        - `commands.cooldown`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.cooldown
        - `commands.BucketType`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.BucketType
        """
        await ctx.send("Cooldown command executed successfully! It's now on cooldown for you for 30 seconds.")

    # ==================================================
    # EXAMPLE SUBGROUP COMMAND WITH ITS OWN SUBCOMMANDS
    # ==================================================

    # Defines a subgroup 'example' under the main 'demo' group.
    @demo.group(invoke_without_command=True, name="example")
    @commands.guild_only()  # Ensures this command and its subcommands run only in servers.
    @checks.has_pl(1)  # Example of a custom check defined in `tux.utils.checks`. Requires Permission Level 1+.
    async def demo_example_group(self, ctx: commands.Context[Tux]) -> None:
        """
        A group command demonstrating nested commands and custom checks.

        Invoked via `demo example`. When called without a subcommand, it displays help info.
        It uses a custom permission level check (`has_pl`) from the project's utilities.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.

        Ref:
        - `commands.guild_only`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.guild_only
        - Custom Checks: (Refer to `tux/utils/checks.py`)
        """
        # Using EmbedCreator for consistency.
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="Demo Group: `example`",
            description="This is a demonstration of a command group with subcommands.",
        )

        # Dynamically accessing subcommands (if needed, though manual listing is clearer here)
        # subcommands = ", ".join(f"`{cmd.name}`" for cmd in self.demo_example_group.commands)
        # embed.add_field(name="Available Subcommands", value=subcommands or "None", inline=False)

        # Corrected multi-line value
        embed.add_field(name="Subcommands", value="`demo example sub1`\n`demo example sub2`", inline=False)
        embed.add_field(
            name="Required Access",
            value="Requires Permission Level 1+ (e.g., Support role).",
            inline=False,
        )

        await ctx.send(embed=embed, delete_after=CONST.DEFAULT_DELETE_AFTER)

    @demo_example_group.command(name="sub1")
    async def demo_example_sub1(self, ctx: commands.Context[Tux], *, message: str = "Default message!") -> None:
        """
        Subcommand `demo example sub1`. Demonstrates optional arguments.

        Takes an optional message; if not provided, uses a default value.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        message : str, optional
            Message provided by the user, defaults to "Default message!".
        """
        # Using try/except within commands is good practice for localized error handling,
        # although the cog-level handler provides a fallback.
        try:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.SUCCESS,
                title="Demo Subcommand: `sub1` Executed",
                description=f"You said: {message}",
            )
            await ctx.send(embed=embed)
        except Exception as error:
            logger.error(f"Error in demo_example_sub1: {error}", exc_info=True)
            # Inform user specifically about this command failing.
            await ctx.send("Oops! Something went wrong with the `sub1` command.")

    @demo_example_group.command(name="sub2")
    async def demo_example_sub2(self, ctx: commands.Context[Tux], user: discord.Member) -> None:
        """
        Subcommand `demo example sub2`. Demonstrates required arguments and converters.

        Requires a `discord.Member` object as input. Discord.py automatically handles
        converting user input (like mentions, IDs, names) into a Member object.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        user : discord.Member
            The server member specified by the user.

        Ref:
        - Converters (like `discord.Member`): https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#converters
        """
        try:
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title="Demo Subcommand: `sub2` Info",
                description=f"Showing details for user: {user.mention}",
            )

            embed.set_thumbnail(url=user.display_avatar.url)  # Use display_avatar for server-specific avatar
            embed.add_field(name="User ID", value=user.id, inline=True)
            embed.add_field(name="Display Name", value=user.display_name, inline=True)  # Server nickname or username

            # Use the project's utility for consistent timestamp formatting.
            embed.add_field(name="Account Created", value=datetime_to_unix(user.created_at), inline=True)
            if user.joined_at:  # joined_at can be None in rare cases
                embed.add_field(name="Joined Server", value=datetime_to_unix(user.joined_at), inline=True)

            await ctx.send(embed=embed)
        except commands.MemberNotFound as e:  # Specific error handling for bad input
            await ctx.send(
                f"Could not find a member matching '{e.argument}'. Please provide a valid mention, ID, or name.",
            )
        except Exception as error:
            logger.error(f"Error in demo_example_sub2: {error}", exc_info=True)
            await ctx.send("Oops! Something went wrong trying to get user info for `sub2`.")

    # ==================================================
    # HYBRID COMMAND EXAMPLES
    # ==================================================
    # Hybrid commands can be invoked via prefix or as slash commands.

    # Defines a hybrid command 'demo_ping'.
    @commands.hybrid_command(name="demo_ping", description="Checks the bot's latency.")
    @commands.cooldown(1, 5, commands.BucketType.user)  # Cooldown applies to both invocation methods.
    async def demo_ping(self, ctx: commands.Context[Tux]) -> None:
        """
        A hybrid command showing bot latency.

        Uses `@commands.hybrid_command` decorator. Works as `demo demo_ping` and `/demo_ping`.
        Accesses `bot.latency` to get the websocket latency.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object (can be traditional Context or Interaction context).

        Ref:
        - `@commands.hybrid_command`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.hybrid_command
        - `Bot.latency`: https://discordpy.readthedocs.io/en/stable/api.html#discord.Client.latency
        - `Context.send`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context.send (Handles both Interaction and Message contexts)
        """
        try:
            latency_ms = round(self.bot.latency * 1000)

            # Determine status/color based on latency value.
            # Using project constants for colors ensures consistency.
            if latency_ms < 100:
                color = CONST.EMBED_COLORS.get("SUCCESS", discord.Color.green())
                status = "Excellent"
            elif latency_ms < 200:
                color = CONST.EMBED_COLORS.get("INFO", discord.Color.blue())
                status = "Good"
            else:
                color = CONST.EMBED_COLORS.get("WARNING", discord.Color.orange())
                status = "Okay"  # Avoid overly negative terms like "Poor" unless very high

            embed = discord.Embed(
                title="🏓 Pong!",
                description=f"Current websocket latency: **{latency_ms}ms** ({status})",
                color=color,
            )
            # `ctx.send` works seamlessly for both hybrid invocation types.
            # `ephemeral=True` could be used for slash commands to make the response visible only to the user.
            # Check if the context has an interaction attribute (indicating slash command usage)
            is_interaction = ctx.interaction is not None
            await ctx.send(embed=embed, ephemeral=is_interaction)
        except Exception as error:
            logger.error(f"Error in hybrid command demo_ping: {error}", exc_info=True)
            await ctx.send("An error occurred while calculating latency.")

    # Note: This 'userinfo' is currently a prefix command.
    # To make it hybrid, replace `@demo.command` with `@commands.hybrid_command`
    # and potentially adjust argument handling if slash-specific features are needed.
    @demo.command(name="userinfo", description="Displays information about a user.")
    @commands.guild_only()  # Good practice for commands needing member info.
    async def demo_userinfo(self, ctx: commands.Context[Tux], user: discord.Member | None = None) -> None:
        """
        Display information about a server member (or the invoker).

        Demonstrates optional arguments and fetching user/member details.
        Uses `discord.Member` converter. Defaults to the command author if no user is specified.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        user : discord.Member | None, optional
            The member to get info about. If None, defaults to `ctx.author`.

        Ref:
        - Optional arguments: https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#optional-arguments
        - `discord.Member`: https://discordpy.readthedocs.io/en/stable/api.html#discord.Member
        - `ctx.author`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Context.author
        """
        # Default to the author if no user argument is provided.
        # `guild_only` ensures ctx.author is a Member, but `cast` clarifies type for static analysis.
        target_user = user or cast(discord.Member, ctx.author)

        try:
            # Use EmbedCreator for standard embed format.
            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title=f"User Info: {target_user.display_name}",  # Shows nickname if set
                description=f"Details for {target_user.mention} (`{target_user.id}`)",
                thumbnail_url=target_user.display_avatar.url,  # Server-specific avatar if set
            )

            # Basic info fields
            embed.add_field(name="Username", value=str(target_user), inline=True)  # username#discriminator or username
            embed.add_field(name="Is Bot?", value="✅ Yes" if target_user.bot else "❌ No", inline=True)

            # Timestamps using the utility function for consistency
            embed.add_field(name="Account Created", value=datetime_to_unix(target_user.created_at), inline=True)
            if target_user.joined_at:  # Should always be present due to guild_only and Member type
                embed.add_field(name="Joined Server", value=datetime_to_unix(target_user.joined_at), inline=True)

            if roles := sorted(
                [role for role in target_user.roles if role.name != "@everyone"],
                key=lambda r: r.position,
                reverse=True,
            ):
                role_limit = 10
                role_mentions = ", ".join(r.mention for r in roles[:role_limit])
                if len(roles) > role_limit:
                    role_mentions += f" (+{len(roles) - role_limit} more)"
                embed.add_field(name=f"Roles [{len(roles)}]", value=role_mentions or "None", inline=False)
            else:
                embed.add_field(name="Roles", value="No roles other than @everyone.", inline=False)

            # Add top role and server avatar info
            embed.add_field(name="Top Role", value=target_user.top_role.mention, inline=True)
            if target_user.guild_avatar:
                embed.add_field(name="Has Server Avatar?", value="✅ Yes", inline=True)

            await ctx.send(embed=embed)
        except Exception as error:
            logger.error(f"Error in demo_userinfo: {error}", exc_info=True)
            await ctx.send("An error occurred while retrieving user information.")

    # ==================================================
    # CALCULATOR HYBRID GROUP COMMAND EXAMPLE
    # ==================================================

    # Define calc as a top-level hybrid group.
    # Use aliases to allow `demo calc ...` prefix invocation.
    @commands.hybrid_group(
        name="calc",
        aliases=["demo calc"],  # Allows `demo calc ...` via prefix
        description="Performs simple calculations.",
        invoke_without_command=True,
    )
    async def demo_calc(self, ctx: commands.Context[Tux]) -> None:
        """
        A hybrid command group for calculator functions.

        Invoked via `demo calc ...` (prefix) or `/calc ...` (slash).
        Shows help when called without a subcommand (`demo calc` or `/calc`).
        Subcommands (`add`, `subtract`, etc.) are also hybrid.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.

        Ref:
        - `@commands.hybrid_group`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.hybrid_group
        - Command Aliases: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Command.aliases
        """
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="🧮 Calculator Commands (`/calc` or `demo calc`)",
            description="Use subcommands to perform calculations. Works with prefix (`demo calc add 1 2`) or slash (`/calc add num1: 1 num2: 2`).",
        )

        # Listing subcommands manually for clarity. Could also iterate `demo_calc.commands`.
        embed.add_field(name="Addition", value="`add <a> <b>`", inline=True)
        embed.add_field(name="Subtraction", value="`subtract <a> <b>`", inline=True)
        embed.add_field(name="Multiplication", value="`multiply <a> <b>`", inline=True)
        embed.add_field(name="Division", value="`divide <a> <b>`", inline=True)

        await ctx.send(embed=embed)

    # Subcommands inherit the hybrid nature from the parent group.
    # They are attached to `demo_calc`.
    # Invocation: `demo calc add ...` or `/calc add ...`
    @demo_calc.command(name="add", description="Adds two numbers.")
    # Use `app_commands.describe` for slash command argument descriptions.
    @app_commands.describe(a="The first number", b="The second number")
    async def demo_calc_add(self, ctx: commands.Context[Tux], a: float, b: float) -> None:
        """
        Hybrid subcommand: Adds two numbers. Uses float converter.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        a : float
            First number (automatically converted from user input).
        b : float
            Second number (automatically converted).

        Ref:
        - `app_commands.describe`: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.describe
        - Type hints as converters: https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html#converters
        """
        result = a + b
        await ctx.send(f"Result: {a} + {b} = **{result}**")

    @demo_calc.command(name="subtract", description="Subtracts the second number from the first.")
    @app_commands.describe(a="The number to subtract from", b="The number to subtract")
    async def demo_calc_subtract(self, ctx: commands.Context[Tux], a: float, b: float) -> None:
        """Hybrid subcommand: Subtracts two numbers."""
        result = a - b
        await ctx.send(f"Result: {a} - {b} = **{result}**")

    @demo_calc.command(name="multiply", description="Multiplies two numbers.")
    @app_commands.describe(a="The first number", b="The second number")
    async def demo_calc_multiply(self, ctx: commands.Context[Tux], a: float, b: float) -> None:
        """Hybrid subcommand: Multiplies two numbers."""
        result = a * b
        # Using '*' for multiplication to avoid ambiguous character lint errors.
        await ctx.send(f"Result: {a} * {b} = **{result}**")

    @demo_calc.command(name="divide", description="Divides the first number by the second.")
    @app_commands.describe(a="The dividend", b="The divisor")
    async def demo_calc_divide(self, ctx: commands.Context[Tux], a: float, b: float) -> None:
        """
        Hybrid subcommand: Divides two numbers. Includes division-by-zero check.
        """
        # Crucial check for division.
        if b == 0:
            await ctx.send("🚫 Error: Cannot divide by zero.")
            return  # Stop execution

        result = a / b
        # Using '/' for division.
        await ctx.send(f"Result: {a} / {b} = **{result}**")

    # ==================================================
    # DATABASE COMMANDS EXAMPLE
    # ==================================================
    # These commands simulate database interactions using the DatabaseController.
    # Note: Actual database logic resides in the controller/models, not directly here.

    @demo.group(name="db", invoke_without_command=True)
    @commands.guild_only()  # Assumes DB operations are often guild-specific.
    async def demo_db(self, ctx: commands.Context[Tux]) -> None:
        """
        Command group for demonstrating database interactions.

        Uses simulated data fetched/updated via the `DatabaseController`.
        Shows help when invoked without a subcommand.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title="🗄️ Database Interaction Demos",
            # Corrected multi-line description
            description=(
                "These commands demonstrate simulated interactions with the bot's database.\n"
                "Actual database logic is handled by controllers (`tux.database.controllers`).\n\n"
                "**Usage:** `demo db <subcommand> [arguments]`"
            ),
        )

        embed.add_field(name="View Profile", value="`demo db profile [user]`", inline=False)
        embed.add_field(name="View Guild Config", value="`demo db guild`", inline=False)
        embed.add_field(name="Update Bio", value="`demo db bio <your new bio>`", inline=False)
        embed.add_field(name="Show Stats", value="`demo db stats`", inline=False)

        await ctx.send(embed=embed)

    @demo_db.command(name="profile", description="Displays a simulated user profile from the DB.")
    @app_commands.describe(user="The user whose profile to view (defaults to you).")
    async def demo_db_profile(self, ctx: commands.Context[Tux], user: discord.Member | None = None) -> None:
        """
        Simulates fetching and displaying a user profile from the database.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        user : discord.Member, optional
            The user whose profile to show. Defaults to `ctx.author`.
        """
        target_user = user or cast(discord.Member, ctx.author)

        # In a real scenario, this would call a method like `self._db.users.get_profile(target_user.id)`
        try:
            # Simulate data that might be stored in a user profile table.
            # Placeholder methods for demonstration
            # Simplified simulation to avoid type checker issues with getattr/lambda
            simulated_data = {
                "user_id": target_user.id,
                "xp": 1234,  # Simulated value
                "level": 5,  # Simulated value
                "bio": "This is a simulated bio.",  # Simulated value
                "commands_used": 42,  # Simulated
                "last_active": datetime.now(UTC).strftime("%Y-%m-%d %H:%M"),  # Simulated
            }

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title=f"Simulated Profile: {target_user.display_name}",
                description=str(simulated_data["bio"]),
                thumbnail_url=target_user.display_avatar.url,
            )

            embed.add_field(name="Level", value=str(simulated_data["level"]), inline=True)
            embed.add_field(name="XP", value=str(simulated_data["xp"]), inline=True)
            embed.add_field(name="Commands Used", value=str(simulated_data["commands_used"]), inline=True)
            embed.add_field(name="Simulated Last Active", value=simulated_data["last_active"], inline=True)

            await ctx.send(embed=embed)

        except Exception as error:
            logger.error(f"Error simulating DB profile fetch for {target_user.id}: {error}", exc_info=True)
            await ctx.send("An error occurred while fetching the simulated profile.")

    @demo_db.command(name="guild", description="Displays simulated guild configuration from the DB.")
    async def demo_db_guild(self, ctx: commands.Context[Tux]) -> None:
        """
        Simulates fetching and displaying guild configuration from the database.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """
        # `guild_only` check at the group level ensures ctx.guild is not None.
        # Added assertion for type safety/clarity.
        assert ctx.guild is not None, "Guild context is expected here."

        try:
            # Simulate fetching guild-specific settings.
            # Real call might be `self._db.guilds.get_config(ctx.guild.id)`
            # Using placeholders for demonstration
            # Simplified simulation
            simulated_config = {
                "guild_id": ctx.guild.id,
                "prefix": "!",  # Simulated value, assuming '!' as default
                "welcome_channel_id": "123456789012345678",  # Simulated ID
                "log_channel_id": None,  # Simulated
                "mute_role_id": None,  # Simulated
            }

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title=f"Simulated Config: {ctx.guild.name}",
                description="Current simulated server configuration.",
                thumbnail_url=ctx.guild.icon.url if ctx.guild.icon else None,
            )

            embed.add_field(name="Command Prefix", value=f"`{simulated_config['prefix']}`", inline=True)

            # Display channel/role settings, handling cases where they aren't set.
            wc_id = simulated_config["welcome_channel_id"]
            welcome_channel = f"<#{wc_id}>" if wc_id else "Not set"
            embed.add_field(name="Welcome Channel", value=welcome_channel, inline=True)

            lc_id = simulated_config["log_channel_id"]
            log_channel = f"<#{lc_id}>" if lc_id else "Not set"
            embed.add_field(name="Log Channel", value=log_channel, inline=True)

            mr_id = simulated_config["mute_role_id"]
            mute_role = f"<@&{mr_id}>" if mr_id else "Not set"
            embed.add_field(name="Mute Role", value=mute_role, inline=True)

            await ctx.send(embed=embed)

        except Exception as error:
            logger.error(f"Error simulating DB guild config fetch for {ctx.guild.id}: {error}", exc_info=True)
            await ctx.send("An error occurred while fetching the simulated guild configuration.")

    @demo_db.command(name="bio", description="Updates your simulated profile bio in the DB.")
    @app_commands.describe(bio="Your new bio (max 250 characters).")
    async def demo_db_bio(self, ctx: commands.Context[Tux], *, bio: str) -> None:
        """
        Simulates updating a user's bio in the database.

        Demonstrates input validation (length check) before attempting an update.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        bio : str
            The new bio text provided by the user.
        """
        # Input validation is crucial before database operations.
        max_bio_length = 250
        if len(bio) > max_bio_length:
            await ctx.send(f"❌ Error: Bio is too long! Maximum length is {max_bio_length} characters.")
            return

        try:
            # Simulate the update operation.
            # Real call: `await self._db.users.update_bio(ctx.author.id, bio)`
            # Using placeholder for demonstration
            # Simplified simulation - assume success
            success = True

            if success:
                # Corrected f-string formatting
                await ctx.send(f'✅ Your simulated bio has been updated to: "{bio}"')
                logger.info(f"User {ctx.author.id} updated simulated bio.")
            else:
                await ctx.send("⚠️ Failed to update simulated bio (simulated failure).")

        except Exception as error:
            logger.error(f"Error simulating DB bio update for {ctx.author.id}: {error}", exc_info=True)
            await ctx.send("An error occurred while updating your simulated bio.")

    @demo_db.command(name="stats", description="Displays simulated database statistics.")
    async def demo_db_stats(self, ctx: commands.Context[Tux]) -> None:
        """
        Simulates fetching and displaying aggregated database statistics.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """
        try:
            # Simulate fetching aggregated data.
            # Real calls might involve counts from multiple tables:
            # `self._db.users.count()`, `self._db.guilds.count()`, etc.
            # Using placeholder for demonstration
            # Simplified simulation
            simulated_stats = {"users": 1250, "guilds": 15, "commands_executed": 12500, "warnings_issued": 150}

            embed = EmbedCreator.create_embed(
                embed_type=EmbedType.INFO,
                title="📊 Simulated Database Statistics",
                description="Overview of simulated data counts across the bot.",
            )

            # Use f-string formatting for numbers
            embed.add_field(name="Tracked Users", value=f"{simulated_stats.get('users', 0):,}", inline=True)
            embed.add_field(name="Guild Configs", value=f"{simulated_stats.get('guilds', 0):,}", inline=True)
            embed.add_field(
                name="Commands Logged",
                value=f"{simulated_stats.get('commands_executed', 0):,}",
                inline=True,
            )
            embed.add_field(name="Warnings Issued", value=f"{simulated_stats.get('warnings_issued', 0):,}", inline=True)
            # Add more simulated stats as needed...

            embed.set_footer(
                text=f"Simulated data | Last updated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            )

            await ctx.send(embed=embed)

        except Exception as error:
            logger.error(f"Error simulating DB stats fetch: {error}", exc_info=True)
            await ctx.send("An error occurred while fetching simulated database statistics.")

    # ==================================================
    # SLASH COMMAND EXAMPLES (using discord.app_commands)
    # ==================================================
    # These commands are *only* available as slash commands.

    # Defines an application command group 'fruit'.
    # Grouping helps organize related slash commands in the UI.
    # `guild_only=True` restricts this group and its commands to servers.
    fruit_group = app_commands.Group(name="fruit", description="Fruit-related slash commands", guild_only=True)

    # Defines a basic slash command.
    @app_commands.command(name="greet", description="Sends a friendly greeting via slash command.")
    @app_commands.guild_only()  # Redundant if group is guild_only, but good practice for clarity.
    @app_commands.describe(user="The user you want to greet.")  # Descriptions appear in the Discord UI.
    async def app_greet(self, interaction: discord.Interaction, user: discord.Member) -> None:
        """
        A simple slash command demonstrating interaction response and member arguments.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object representing the slash command invocation.
            Used to respond to the command.
        user : discord.Member
            The member selected by the user invoking the command.

        Ref:
        - `@app_commands.command`: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.command
        - `discord.Interaction`: https://discordpy.readthedocs.io/en/stable/api.html#discord.Interaction
        - `InteractionResponse.send_message`: https://discordpy.readthedocs.io/en/stable/api.html#discord.InteractionResponse.send_message
        """
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.SUCCESS,
            title="👋 Hello!",
            description=f"{interaction.user.mention} says hello to {user.mention}!",
        )
        # Use `interaction.response.send_message` for the initial response to a slash command.
        # `ephemeral=True` makes the response visible only to the invoking user.
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Demonstrates using `app_commands.choices` for parameters.
    @app_commands.command(name="choose_fruit", description="Choose your favorite fruit and rate it.")
    @app_commands.describe(fruit="Select your favorite fruit from the list.", rating="How much do you like this fruit?")
    # Separate choices decorators for parameters with different value types (str vs int).
    @app_commands.choices(
        fruit=[
            app_commands.Choice(name="🍎 Apple", value="apple"),
            app_commands.Choice(name="🍌 Banana", value="banana"),
            app_commands.Choice(name="🍒 Cherry", value="cherry"),
            app_commands.Choice(name="🥝 Kiwi", value="kiwi"),
        ],
    )
    @app_commands.choices(
        rating=[
            app_commands.Choice(name="⭐ (Bad)", value=1),
            app_commands.Choice(name="⭐⭐ (Okay)", value=2),
            app_commands.Choice(name="⭐⭐⭐ (Good)", value=3),
            app_commands.Choice(name="⭐⭐⭐⭐ (Great)", value=4),
            app_commands.Choice(name="⭐⭐⭐⭐⭐ (Amazing!)", value=5),
        ],
    )
    # Type hint uses the value type from the Choice
    async def choose_fruit(
        self,
        interaction: discord.Interaction,
        fruit: app_commands.Choice[str],
        rating: app_commands.Choice[int],
    ) -> None:
        """
        Slash command demonstrating static choices for arguments.

        The user selects from predefined lists in the Discord UI.
        The `value` of the choice is passed to the command function.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        fruit : app_commands.Choice[str]
            The selected fruit choice object. Access value with `fruit.value`, name with `fruit.name`.
        rating : app_commands.Choice[int]
            The selected rating choice object. Access value with `rating.value`.

        Ref:
        - `@app_commands.choices`: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.choices
        - `app_commands.Choice`: https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.app_commands.Choice
        """
        await interaction.response.send_message(
            f"You chose **{fruit.name}** (value: `{fruit.value}`) and rated it **{rating.value}/5** stars!",
            ephemeral=True,
        )

    # Autocomplete example needs to be added here
    # @app_commands.command(name="search_fruit", description="Search for a fruit with autocomplete.")
    # @app_commands.describe(query="Start typing the name of a fruit.")
    # async def search_fruit(self, interaction: discord.Interaction, query: str):
    #     ... # Implementation using the autocomplete decorator
    #
    # @search_fruit.autocomplete('query')
    # async def fruit_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    #     # Filter FRUIT_CHOICES based on 'current' input and return matching Choices
    #     choices = [
    #         app_commands.Choice(name=fruit, value=fruit)
    #         for fruit in FRUIT_CHOICES if current.lower() in fruit.lower()
    #     ]
    #     return choices[:25] # Discord limits autocomplete choices to 25

    # Defines a command 'info' within the 'fruit_group'. Accessed via `/fruit info`.
    @fruit_group.command(name="info", description="Get a short description of a fruit.")
    # Using Literal[...] provides choices based on the Literal values.
    # Good for a fixed, known set of string options.
    @app_commands.describe(name="The name of the fruit to get info about.")
    async def fruit_info(
        self,
        interaction: discord.Interaction,
        name: Literal["Apple", "Banana", "Cherry", "Kiwi", "Mango", "Orange", "Pineapple"],
    ) -> None:
        """
        Slash subcommand (`/fruit info`) demonstrating Literal for choices.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction object.
        name : Literal["Apple", ..., "Pineapple"]
            The fruit name selected by the user, guaranteed to be one of the Literal values.

        Ref:
        - App Command Groups: https://discordpy.readthedocs.io/en/stable/interactions/api.html#application-command-groups
        - Using Literal for Choices: https://discordpy.readthedocs.io/en/stable/interactions/api.html#using-literal-for-choices
        """
        # Simple dictionary lookup for demonstration descriptions.
        descriptions = {
            "Apple": "🍎 A crisp, round fruit. Keeps the doctor away!",
            "Banana": "🍌 A long, yellow fruit, rich in potassium.",
            "Cherry": "🍒 Small, round, red or black fruit with a stone.",
            "Kiwi": "🥝 Fuzzy brown skin, green flesh, tiny black seeds.",
            "Mango": "🥭 Sweet tropical fruit with a large pit.",
            "Orange": "🍊 Round citrus fruit, known for Vitamin C.",
            "Pineapple": "🍍 Tropical fruit with a spiky skin and sweet inside.",
        }
        description = descriptions.get(name, "❓ Information not found for this fruit.")

        await interaction.response.send_message(f"**{name}**: {description}", ephemeral=True)


# Standard Cog setup function
# This async function is called by the bot's loading mechanism (e.g., `bot.load_extension`).
# It's essential for registering the Cog and its commands with the bot.
async def setup(bot: Tux) -> None:
    """
    Adds the DemoCog to the bot.

    This is the required entry point for any cog extension file.
    It creates an instance of the cog and uses `bot.add_cog` to register it.

    Parameters
    ----------
    bot : Tux
        The bot instance.

    Ref:
    - Cog Setup: https://discordpy.readthedocs.io/en/stable/ext/commands/cogs.html#setup
    - `Bot.add_cog`: https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.ext.commands.Bot.add_cog
    """
    await bot.add_cog(DemoCog(bot))
    logger.info("DemoCog loaded successfully.")  # Good practice to log cog loading
