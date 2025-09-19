"""Command suggestion utilities for error handling."""

import contextlib

import discord
import Levenshtein
from discord.ext import commands

from tux.core.bot import Tux

from .config import SUGGESTION_DELETE_AFTER


class CommandSuggester:
    """Handles command suggestions when commands are not found."""

    def __init__(self, config_delete_after: int = SUGGESTION_DELETE_AFTER):
        self.delete_after = config_delete_after

    async def suggest_command(self, ctx: commands.Context[Tux]) -> list[str] | None:
        """
        Attempts to find similar command names when a CommandNotFound error occurs.

        This method uses fuzzy string matching to find commands that are similar
        to what the user typed, helping them discover the correct command name.

        Args:
            ctx: The command context containing the failed command attempt.

        Returns:
            A list of suggested command names, or None if no good suggestions are found.
        """
        if not ctx.invoked_with:
            return None

        user_input = ctx.invoked_with.lower()
        all_commands: list[str] = []

        # Collect all available commands (including subcommands)
        for command in ctx.bot.walk_commands():
            if not command.hidden:
                all_commands.append(command.qualified_name.lower())
                # Also include command aliases
                all_commands.extend(alias.lower() for alias in command.aliases)

        # Remove duplicates while preserving order
        unique_commands: list[str] = []
        seen: set[str] = set()
        for cmd in all_commands:
            if cmd not in seen:
                unique_commands.append(cmd)
                seen.add(cmd)

        # Find similar commands using Levenshtein distance
        suggestions: list[tuple[str, int]] = []
        max_distance = min(3, len(user_input) // 2)  # Allow up to 3 edits or half the input length

        for command_name in unique_commands:
            distance = Levenshtein.distance(user_input, command_name)

            # Consider it a good suggestion if:
            # 1. The edit distance is within our threshold, OR
            # 2. The user input is a substring of the command name, OR
            # 3. The command name starts with the user input
            if distance <= max_distance or user_input in command_name or command_name.startswith(user_input):
                suggestions.append((command_name, distance))

        # Sort by distance (closer matches first) and limit results
        suggestions.sort(key=lambda x: (x[1], len(x[0])))
        final_suggestions: list[str] = [cmd for cmd, _ in suggestions[:5]]  # Limit to top 5 suggestions

        return final_suggestions or None

    async def handle_command_not_found(self, ctx: commands.Context[Tux]) -> None:
        """
        Specific handler for the `CommandNotFound` error.

        When a user types a command that doesn't exist, this method attempts
        to find similar commands and suggests them to the user.

        Args:
            ctx: The command context for the failed command.
        """
        suggestions = await self.suggest_command(ctx)

        if not suggestions:
            return

        # Create embed with suggestions
        embed = discord.Embed(
            title="Command Not Found",
            description=f"The command `{ctx.invoked_with}` was not found.",
            color=discord.Color.blue(),
        )

        # Format suggestions
        suggestion_text = "\n".join(f"• `{ctx.prefix}{suggestion}`" for suggestion in suggestions)
        embed.add_field(
            name="Did you mean?",
            value=suggestion_text,
            inline=False,
        )

        # Send the suggestion message
        with contextlib.suppress(discord.HTTPException):
            await ctx.send(embed=embed, delete_after=self.delete_after)
