"""
Dynamic moderation command configuration system.

This module provides a configuration-driven approach to moderation commands,
allowing for DRY implementation and consistent behavior across all moderation actions.
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

import discord

from prisma.enums import CaseType
from tux.utils.mixed_args import generate_mixed_usage


@dataclass
class ModerationCommandConfig:
    """
    Configuration for a moderation command.

    This dataclass defines all the behavior and parameters for a moderation command,
    allowing for dynamic command generation and consistent behavior.
    """

    # Basic command info
    name: str
    aliases: list[str]
    description: str

    # Case and permission info
    case_type: CaseType
    required_permission_level: int

    # Argument support flags
    supports_duration: bool
    supports_purge: bool
    supports_reason: bool
    supports_silent: bool

    # Action configuration
    dm_action: str  # e.g., "banned", "timed out", "kicked"
    discord_action: Callable[[discord.Guild, discord.Member, str, dict[str, Any]], Coroutine[Any, Any, None]]

    # Validation and checks
    requires_member: bool = True  # False for unban commands
    check_timed_out: bool = False  # Only for timeout commands
    check_already_banned: bool = False  # Only for ban commands

    def get_usage_string(self) -> str:
        """Generate usage string for this command."""
        required_params: list[str] = ["member"] if self.requires_member else []
        optional_params: list[str] = []

        if self.supports_duration:
            optional_params.append("duration")
        if self.supports_reason:
            optional_params.append("reason")

        flags: list[str] = []
        if self.supports_duration:
            flags.append("-d")
        if self.supports_purge:
            flags.append("-p")
        if self.supports_silent:
            flags.append("-s")

        return generate_mixed_usage(self.name, required_params, optional_params, flags)

    def get_help_text(self) -> str:
        """Generate help text for this command."""
        base_text = f"{self.description}\n\n"

        if self.supports_duration and self.supports_reason:
            base_text += "Supports both positional and flag-based arguments:\n"
            base_text += f"- Positional: `{self.name} @user 14d reason`\n"
            base_text += f"- Flag-based: `{self.name} @user reason -d 14d`\n"
            base_text += f"- Mixed: `{self.name} @user 14d reason -s`\n"
        elif self.supports_reason:
            base_text += "Supports both positional and flag-based arguments:\n"
            base_text += f"- Positional: `{self.name} @user reason`\n"
            base_text += f"- Flag-based: `{self.name} @user -r reason`\n"

        return base_text


# Command registry - defines all moderation commands
MODERATION_COMMANDS: dict[str, ModerationCommandConfig] = {
    "ban": ModerationCommandConfig(
        name="ban",
        aliases=["b"],
        description="Ban a member from the server.",
        case_type=CaseType.BAN,
        required_permission_level=3,
        supports_duration=False,
        supports_purge=True,
        supports_reason=True,
        supports_silent=True,
        dm_action="banned",
        discord_action=lambda guild, member, reason, args: guild.ban(
            member,
            reason=reason,
            delete_message_seconds=args.get("purge", 0) * 86400,
        ),
        check_already_banned=True,
    ),
    "tempban": ModerationCommandConfig(
        name="tempban",
        aliases=["tb"],
        description="Temporarily ban a member from the server.",
        case_type=CaseType.TEMPBAN,
        required_permission_level=3,
        supports_duration=True,
        supports_purge=True,
        supports_reason=True,
        supports_silent=True,
        dm_action="temporarily banned",
        discord_action=lambda guild, member, reason, args: guild.ban(
            member,
            reason=reason,
            delete_message_seconds=args.get("purge", 0) * 86400,
        ),
        check_already_banned=True,
    ),
    "kick": ModerationCommandConfig(
        name="kick",
        aliases=["k"],
        description="Kick a member from the server.",
        case_type=CaseType.KICK,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="kicked",
        discord_action=lambda guild, member, reason, args: guild.kick(member, reason=reason),
    ),
    "timeout": ModerationCommandConfig(
        name="timeout",
        aliases=["t", "to", "mute", "m"],
        description="Timeout a member from the server.",
        case_type=CaseType.TIMEOUT,
        required_permission_level=2,
        supports_duration=True,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="timed out",
        discord_action=lambda guild, member, reason, args: member.timeout(args.get("duration"), reason=reason),
        check_timed_out=True,
    ),
    "warn": ModerationCommandConfig(
        name="warn",
        aliases=["w"],
        description="Warn a member.",
        case_type=CaseType.WARN,
        required_permission_level=1,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="warned",
        discord_action=lambda guild, member, reason, args: None,  # No Discord action for warns
    ),
    "jail": ModerationCommandConfig(
        name="jail",
        aliases=["j"],
        description="Jail a member (remove all roles and add jail role).",
        case_type=CaseType.JAIL,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="jailed",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
    "unjail": ModerationCommandConfig(
        name="unjail",
        aliases=["uj"],
        description="Unjail a member (restore original roles).",
        case_type=CaseType.UNJAIL,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="unjailed",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
    "unban": ModerationCommandConfig(
        name="unban",
        aliases=["ub"],
        description="Unban a user from the server.",
        case_type=CaseType.UNBAN,
        required_permission_level=3,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        requires_member=False,
        dm_action="unbanned",
        discord_action=lambda guild, member, reason, args: guild.unban(member, reason=reason),
    ),
    "untimeout": ModerationCommandConfig(
        name="untimeout",
        aliases=["ut"],
        description="Remove timeout from a member.",
        case_type=CaseType.UNTIMEOUT,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="untimeout",
        discord_action=lambda guild, member, reason, args: member.timeout(None, reason=reason),
    ),
    "snippetban": ModerationCommandConfig(
        name="snippetban",
        aliases=["sb"],
        description="Ban a user from using snippets.",
        case_type=CaseType.SNIPPETBAN,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="snippet banned",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
    "snippetunban": ModerationCommandConfig(
        name="snippetunban",
        aliases=["sub"],
        description="Unban a user from using snippets.",
        case_type=CaseType.SNIPPETUNBAN,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="snippet unbanned",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
    "pollban": ModerationCommandConfig(
        name="pollban",
        aliases=["pb"],
        description="Ban a user from creating polls.",
        case_type=CaseType.POLLBAN,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="poll banned",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
    "pollunban": ModerationCommandConfig(
        name="pollunban",
        aliases=["pub"],
        description="Unban a user from creating polls.",
        case_type=CaseType.POLLUNBAN,
        required_permission_level=2,
        supports_duration=False,
        supports_purge=False,
        supports_reason=True,
        supports_silent=True,
        dm_action="poll unbanned",
        discord_action=lambda guild, member, reason, args: None,  # Handled in base class
    ),
}


# This file is a data-only module; provide a noop setup so the cog loader is satisfied.
async def setup(bot):  # type: ignore[unused-argument]
    return
