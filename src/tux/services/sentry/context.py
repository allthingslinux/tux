"""Context management for Sentry events."""

from __future__ import annotations

import time
from typing import Any

import discord
import sentry_sdk
from discord import Interaction
from discord.ext import commands

from .config import is_initialized

# Type alias for a command context or an interaction.
ContextOrInteraction = commands.Context[commands.Bot] | Interaction

# Store command start times for performance tracking
_command_start_times: dict[str, float] = {}


def set_user_context(user: discord.User | discord.Member) -> None:
    """
    Set user context for Sentry events using Discord user information.

    This function identifies users in Sentry using their Discord user ID as the
    primary identifier. This enables user-based filtering, grouping, and analytics
    in Sentry, allowing you to see which users encountered errors.

    Parameters
    ----------
    user : discord.User | discord.Member
        The Discord user to set as context. Must have an `id` attribute.

    Notes
    -----
    The user ID (Discord snowflake) is used as Sentry's user identifier, enabling:
    - User-based error grouping and filtering
    - User impact analysis (how many users affected)
    - User-specific error tracking
    - User analytics in Sentry Insights

    Additional Discord-specific data is included as custom user attributes:
    - Username and display name for better identification
    - Guild information (if member)
    - Permissions and roles (if member)
    - Bot/system flags
    """
    if not is_initialized():
        return

    # Primary identifier: Discord user ID (required by Sentry)
    user_data = {
        "id": str(user.id),  # Discord user ID - used as unique identifier in Sentry
        "username": user.name,  # Discord username
        "display_name": user.display_name,  # Display name (nickname or username)
        "bot": user.bot,  # Whether user is a bot
        "system": getattr(user, "system", False),  # Whether user is a system user
    }

    # Additional Discord-specific context (if member with guild)
    if isinstance(user, discord.Member) and user.guild:
        user_data.update(
            {
                "guild_id": str(user.guild.id),
                "guild_name": user.guild.name,
                "guild_member_count": str(user.guild.member_count),
                "guild_permissions": str(user.guild_permissions.value),
                "top_role": user.top_role.name if user.top_role else None,
            },
        )
        if user.joined_at:
            user_data["joined_at"] = user.joined_at.isoformat()

    sentry_sdk.set_user(user_data)


def set_tag(key: str, value: Any) -> None:
    """Set a tag in the current Sentry scope."""
    if not is_initialized():
        return
    sentry_sdk.set_tag(key, value)


def set_context(key: str, value: dict[str, Any]) -> None:
    """Set context data in the current Sentry scope."""
    if not is_initialized():
        return
    sentry_sdk.set_context(key, value)


def set_command_context(ctx: ContextOrInteraction) -> None:
    """Set command context for Sentry events."""
    if not is_initialized():
        return

    if isinstance(ctx, commands.Context):
        _set_command_context_from_ctx(ctx)
    else:
        _set_command_context_from_interaction(ctx)


def track_command_start(command_name: str) -> None:
    """Track command execution start time."""
    _command_start_times[command_name] = time.perf_counter()


def track_command_end(
    command_name: str,
    success: bool,
    error: Exception | None = None,
) -> None:
    """Track command execution end and performance metrics."""
    if not is_initialized():
        return

    execution_time_ms = 0.0
    if start_time := _command_start_times.pop(command_name, None):
        execution_time = time.perf_counter() - start_time
        execution_time_ms = round(execution_time * 1000, 2)
        set_tag("command.execution_time_ms", execution_time_ms)

    set_tag("command.success", success)
    if error:
        set_tag("command.error_type", type(error).__name__)
        set_context(
            "command_error",
            {
                "error_message": str(error),
                "error_type": type(error).__name__,
                "error_module": getattr(type(error), "__module__", "unknown"),
            },
        )

    # Record metrics for command execution
    # Note: command_type detection would require passing context, defaulting to "unknown"
    # This can be enhanced later by modifying track_command_end signature
    from .metrics import record_command_metric  # noqa: PLC0415

    record_command_metric(
        command_name=command_name,
        execution_time_ms=execution_time_ms,
        success=success,
        error_type=type(error).__name__ if error else None,
        command_type="unknown",  # Could be enhanced to detect prefix/slash from context
    )


def _set_command_context_from_ctx(ctx: commands.Context[commands.Bot]) -> None:
    """Set context from a command context."""
    command_data = {
        "command": ctx.command.qualified_name if ctx.command else "unknown",
        "message_id": str(ctx.message.id),
        "channel_id": str(ctx.channel.id) if ctx.channel else None,
        "guild_id": str(ctx.guild.id) if ctx.guild else None,
        "prefix": ctx.prefix,
        "invoked_with": ctx.invoked_with,
    }

    # Add command arguments
    if ctx.args:
        command_data["args_count"] = str(len(ctx.args))
        command_data["args"] = str([str(arg) for arg in ctx.args[1:]])  # Skip self
    if ctx.kwargs:
        command_data["kwargs"] = str({k: str(v) for k, v in ctx.kwargs.items()})

    if ctx.guild:
        command_data |= {
            "guild_name": ctx.guild.name,
            "guild_member_count": str(ctx.guild.member_count),
            "channel_name": getattr(ctx.channel, "name", None),
            "channel_type": str(ctx.channel.type) if ctx.channel else None,
        }

    set_context("command", command_data)

    command_name = command_data.get("command")
    if command_name and command_name != "unknown":
        track_command_start(command_name)

    if ctx.author:
        set_user_context(ctx.author)


def _set_command_context_from_interaction(interaction: Interaction) -> None:
    """Set context from an interaction."""
    # Lazy import to avoid circular dependency: tux.services.sentry.context → tux.core.context → tux.core.base_cog → tux.database.controllers → tux.database.service → tux.services.sentry
    from tux.core.context import get_interaction_context  # noqa: PLC0415

    interaction_context = get_interaction_context(interaction)

    command_data = {
        "command": interaction_context.get("command", "unknown"),
        "interaction_id": str(interaction.id),
        "channel_id": str(interaction.channel_id) if interaction.channel_id else None,
        "guild_id": str(interaction.guild_id) if interaction.guild_id else None,
        "interaction_type": str(interaction.type),
    }

    # Add interaction data
    if hasattr(interaction, "data") and interaction.data:
        data = interaction.data
        if "options" in data:
            command_data["options"] = str(
                [
                    {
                        "name": option.get("name", "unknown"),
                        "type": option.get("type", "unknown"),
                        "value": option.get("value"),
                    }
                    for option in data["options"]
                ],
            )

    if interaction.guild:
        command_data |= {
            "guild_name": interaction.guild.name,
            "guild_member_count": str(interaction.guild.member_count),
            "channel_name": getattr(interaction.channel, "name", None),
            "channel_type": str(interaction.channel.type)
            if interaction.channel
            else None,
        }

    set_context("interaction", command_data)

    command_name = command_data.get("command")
    if command_name and command_name != "unknown":
        track_command_start(command_name)

    if interaction.user:
        set_user_context(interaction.user)
