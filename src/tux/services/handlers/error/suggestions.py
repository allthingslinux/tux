"""Command suggestion utilities."""

import discord
import Levenshtein
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux

from .config import (
    DEFAULT_MAX_DISTANCE_THRESHOLD,
    DEFAULT_MAX_SUGGESTIONS,
    SHORT_CMD_LEN_THRESHOLD,
    SHORT_CMD_MAX_DISTANCE,
    SHORT_CMD_MAX_SUGGESTIONS,
)


class CommandSuggester:
    """Handles command suggestions for CommandNotFound errors."""

    def __init__(self) -> None:
        """Initialize the command suggester."""

    async def suggest_command(self, ctx: commands.Context[Tux]) -> list[str] | None:
        """Find similar command names using Levenshtein distance.

        Returns
        -------
        list[str] | None
            List of suggested command names, or None if no suggestions found.
        """
        if not ctx.guild or not ctx.invoked_with:
            return None

        command_name = ctx.invoked_with

        # Use stricter limits for short commands
        is_short = len(command_name) <= SHORT_CMD_LEN_THRESHOLD
        max_suggestions = (
            SHORT_CMD_MAX_SUGGESTIONS if is_short else DEFAULT_MAX_SUGGESTIONS
        )
        max_distance = (
            SHORT_CMD_MAX_DISTANCE if is_short else DEFAULT_MAX_DISTANCE_THRESHOLD
        )

        # Find similar commands
        command_distances: dict[str, int] = {}

        for cmd in ctx.bot.walk_commands():
            if cmd.hidden:
                continue

            min_dist = max_distance + 1
            best_name = cmd.qualified_name

            # Check command name and aliases
            names_to_check = [cmd.qualified_name, *cmd.aliases]

            # Also check just the command name without parent for subcommands
            if hasattr(cmd, "name") and cmd.name != cmd.qualified_name:
                names_to_check.append(cmd.name)

            for name in names_to_check:
                distance = Levenshtein.distance(command_name.lower(), name.lower())
                if distance < min_dist:
                    min_dist = distance
                    best_name = (
                        cmd.qualified_name
                    )  # Always use qualified name for suggestions

            # Store if within threshold
            if min_dist <= max_distance:
                current_min = command_distances.get(best_name, max_distance + 1)
                if min_dist < current_min:
                    command_distances[best_name] = min_dist

        if not command_distances:
            return None

        # Sort by distance and return top suggestions
        sorted_suggestions = sorted(command_distances.items(), key=lambda x: x[1])
        return [name for name, _ in sorted_suggestions[:max_suggestions]]

    async def handle_command_not_found(self, ctx: commands.Context[Tux]) -> None:
        """Handle CommandNotFound with suggestions."""
        suggestions = await self.suggest_command(ctx)

        if not suggestions:
            logger.info(f"No suggestions for command '{ctx.invoked_with}'")
            return

        # Format suggestions
        formatted = ", ".join(f"`{ctx.prefix}{s}`" for s in suggestions)
        message = f"Command `{ctx.invoked_with}` not found. Did you mean: {formatted}?"

        # Create embed
        embed = discord.Embed(
            title="Command Not Found",
            description=message,
            color=discord.Color.blue(),
        )

        try:
            await ctx.send(embed=embed)
            logger.info(f"Sent suggestions for '{ctx.invoked_with}': {suggestions}")
        except discord.HTTPException as e:
            logger.error(f"Failed to send suggestions: {e}")
