"""Formatting utilities for Discord objects in info commands."""

from collections.abc import Generator, Iterator
from datetime import UTC, datetime

import discord
from discord.utils import TimestampStyle


def format_bool(value: bool) -> str:
    """Convert boolean to checkmark/cross emoji."""
    return "✅" if value else "❌"


def format_datetime(dt: datetime | None, style: TimestampStyle = "R") -> str:
    """Format datetime to Discord relative format or fallback."""
    if dt is None:
        return "Unknown"
    try:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return discord.utils.format_dt(dt, style)
    except (TypeError, ValueError):
        return "Unknown"


def format_date_long(dt: datetime | None) -> str:
    """Format datetime to long date string (e.g. 'January 25, 2025')."""
    if dt is None:
        return "Unknown"
    try:
        return dt.strftime("%B %d, %Y")
    except (TypeError, ValueError):
        return "Unknown"


def format_permissions(permissions: discord.Permissions) -> str:
    """Format role permissions into a readable string."""
    perm_list = [perm.replace("_", " ").title() for perm, value in permissions if value]
    if not perm_list:
        return "None"
    perm_str = ", ".join(perm_list)
    return f"{perm_str[:1021]}..." if len(perm_str) > 1024 else perm_str


def format_guild_verification_level(level: discord.VerificationLevel) -> str:
    """Format verification level to readable string."""
    verification_names = {
        discord.VerificationLevel.none: "None",
        discord.VerificationLevel.low: "Low",
        discord.VerificationLevel.medium: "Medium",
        discord.VerificationLevel.high: "High",
        discord.VerificationLevel.highest: "Highest",
    }
    return verification_names.get(level, str(level))


def format_guild_nsfw_level(guild: discord.Guild) -> str:
    """Format NSFW level to readable string."""
    if not hasattr(guild, "nsfw_level"):
        return "Unknown"
    nsfw_names = {
        discord.NSFWLevel.default: "Default",
        discord.NSFWLevel.explicit: "Explicit",
        discord.NSFWLevel.safe: "Safe",
        discord.NSFWLevel.age_restricted: "Age Restricted",
    }
    return nsfw_names.get(guild.nsfw_level, str(guild.nsfw_level))


def format_guild_content_filter(level: discord.ContentFilter) -> str:
    """Format content filter level to readable string."""
    content_filter_names = {
        discord.ContentFilter.disabled: "Disabled",
        discord.ContentFilter.no_role: "No Role",
        discord.ContentFilter.all_members: "All Members",
    }
    return content_filter_names.get(level, str(level))


def format_guild_notifications(level: discord.NotificationLevel) -> str:
    """Format notification level to readable string."""
    notification_names = {
        discord.NotificationLevel.all_messages: "All Messages",
        discord.NotificationLevel.only_mentions: "Only Mentions",
    }
    return notification_names.get(level, str(level))


def format_guild_premium_tier(tier: object) -> str:
    """Format premium tier to readable string."""
    try:
        tier_value = int(tier)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return str(tier).replace("_", " ").title()
    else:
        return f"Tier {tier_value}" if tier_value > 0 else "None"


def format_invite_uses(invite: discord.Invite) -> str:
    """Format invite uses to readable string."""
    if invite.max_uses:
        return f"{invite.uses}/{invite.max_uses}"
    return f"{invite.uses}/∞"


def format_invite_max_age(max_age: int | None) -> str:
    """Format invite max age to readable string."""
    if max_age and max_age > 0:
        days = max_age // 86400
        hours = (max_age % 86400) // 3600
        return f"{days}d {hours}h" if days > 0 else f"{hours}h"
    return "Never"


def extract_invite_code(invite_input: str) -> str:
    """Extract invite code from URL or return as-is."""
    invite_input_lower = invite_input.lower()
    if "discord.gg/" in invite_input_lower:
        return invite_input.rsplit("discord.gg/", maxsplit=1)[-1].split(
            "?",
            maxsplit=1,
        )[0]
    if "discord.com/invite/" in invite_input_lower:
        return invite_input.rsplit("discord.com/invite/", maxsplit=1)[-1].split(
            "?",
            maxsplit=1,
        )[0]
    return invite_input


def chunks[T](it: Iterator[T], size: int) -> Generator[list[T]]:
    """Split an iterator into chunks of a specified size."""
    chunk: list[T] = []
    for item in it:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
