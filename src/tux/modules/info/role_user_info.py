"""Role and user helper utilities for info commands."""

from contextlib import suppress

import discord
from loguru import logger

from tux.core.bot import Tux


def get_role_type_info(role: discord.Role) -> list[tuple[str, bool]]:
    """Get role type information."""
    role_type_info: list[tuple[str, bool]] = []
    if hasattr(role, "is_default") and role.is_default():
        role_type_info.append(("Default Role", True))
    if hasattr(role, "is_bot_managed") and role.is_bot_managed():
        role_type_info.append(("Bot Managed", True))
    if hasattr(role, "is_integration") and role.is_integration():
        role_type_info.append(("Integration Managed", True))
    if hasattr(role, "is_premium_subscriber") and role.is_premium_subscriber():
        role_type_info.append(("Premium Subscriber", True))
    if hasattr(role, "is_assignable") and not role.is_assignable():
        role_type_info.append(("Assignable", False))
    return role_type_info


def get_role_tags_info(role: discord.Role) -> list[str] | None:
    """Get role tags information."""
    if not (hasattr(role, "tags") and role.tags):
        return None
    tags = role.tags
    tags_info: list[str] = []
    if hasattr(tags, "bot_id") and tags.bot_id:
        tags_info.append(f"Bot: <@{tags.bot_id}>")
    if hasattr(tags, "integration_id") and tags.integration_id:
        tags_info.append(f"Integration: {tags.integration_id}")
    if hasattr(tags, "subscription_listing_id") and tags.subscription_listing_id:
        tags_info.append("Premium Subscriber Role")
    return tags_info or None


def get_role_flags_info(role: discord.Role) -> list[str] | None:
    """Get role flags information."""
    if not (hasattr(role, "flags") and role.flags):
        return None
    flags = role.flags
    flags_list: list[str] = []
    if hasattr(flags, "inverted") and getattr(flags, "inverted", False):
        flags_list.append("Inverted")
    if hasattr(flags, "mentionable_by_everyone") and getattr(
        flags,
        "mentionable_by_everyone",
        False,
    ):
        flags_list.append("Mentionable by Everyone")
    return flags_list or None


def get_user_banner(user: discord.User) -> str | None:
    """Get the banner URL from a user object."""
    banner = getattr(user, "banner", None)
    return getattr(banner, "url", None)


async def get_member_banner(member: discord.Member, bot: Tux) -> str | None:
    """Get the banner URL from a member's user object (requires fetch)."""
    try:
        user = await bot.fetch_user(member.id)
        banner = getattr(user, "banner", None)
        if banner is not None and hasattr(banner, "url"):
            with suppress(AttributeError, TypeError):
                if url := banner.url:
                    return url
    except discord.NotFound:
        logger.debug(f"User {member.id} not found when fetching banner")
    except discord.HTTPException as e:
        logger.warning(f"Failed to fetch user {member.id} for banner: {e}")
    return None
