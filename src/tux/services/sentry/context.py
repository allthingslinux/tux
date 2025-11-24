"""Context management for Sentry events."""

from __future__ import annotations

import time
from typing import Any

import discord
import sentry_sdk
from discord import Interaction
from discord.ext import commands

from tux.core.context import get_interaction_context

from .config import is_initialized

# Type alias for a command context or an interaction.
ContextOrInteraction = commands.Context[commands.Bot] | Interaction

# Store command start times for performance tracking
_command_start_times: dict[str, float] = {}


def set_user_context(user: discord.User | discord.Member) -> None:
    # sourcery skip: extract-method
    """Set user context for Sentry events."""
    if not is_initialized():
        return

    user_data = {
        "id": str(user.id),
        "username": user.name,
        "display_name": user.display_name,
        "bot": user.bot,
        "system": getattr(user, "system", False),
    }

    if isinstance(user, discord.Member) and user.guild:
        user_data["guild_id"] = str(user.guild.id)
        user_data["guild_name"] = user.guild.name
        user_data["guild_member_count"] = str(user.guild.member_count)
        user_data["guild_permissions"] = str(user.guild_permissions.value)
        user_data["top_role"] = user.top_role.name if user.top_role else None
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

    if start_time := _command_start_times.pop(command_name, None):
        execution_time = time.perf_counter() - start_time
        set_tag("command.execution_time_ms", round(execution_time * 1000, 2))

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
