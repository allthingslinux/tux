"""Helper utilities for formatting and processing Discord objects in info commands."""

from collections.abc import Generator, Iterator
from contextlib import suppress
from datetime import UTC, datetime

import discord
from discord.utils import TimestampStyle
from loguru import logger

from tux.core.bot import Tux
from tux.shared.constants import BANS_LIMIT

# ---- Formatters ----


def format_bool(value: bool) -> str:
    """Convert boolean to checkmark/cross emoji.

    Parameters
    ----------
    value : bool
        The boolean value to format.

    Returns
    -------
    str
        ✅ for True, ❌ for False.
    """
    return "✅" if value else "❌"


def format_datetime(dt: datetime | None, style: TimestampStyle = "R") -> str:
    """Format datetime to Discord relative format or fallback.

    Parameters
    ----------
    dt : datetime | None
        The datetime to format.
    style : TimestampStyle, optional
        The Discord timestamp style, by default "R".

    Returns
    -------
    str
        Formatted Discord timestamp or "Unknown" if None.
    """
    if dt is None:
        return "Unknown"
    try:
        # Ensure UTC-aware datetime (database stores as UTC but returns naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return discord.utils.format_dt(dt, style)
    except (TypeError, ValueError):
        return "Unknown"


def format_date_long(dt: datetime | None) -> str:
    """Format datetime to long date string for Created footers.

    Parameters
    ----------
    dt : datetime | None
        The datetime to format.

    Returns
    -------
    str
        Formatted date (e.g. "January 25, 2025") or "Unknown" if None.
    """
    if dt is None:
        return "Unknown"
    try:
        return dt.strftime("%B %d, %Y")
    except (TypeError, ValueError):
        return "Unknown"


def format_permissions(permissions: discord.Permissions) -> str:
    """Format role permissions into a readable string.

    Parameters
    ----------
    permissions : discord.Permissions
        The permissions to format.

    Returns
    -------
    str
        Formatted permissions string, truncated to 1024 characters if needed.
    """
    perm_list = [perm.replace("_", " ").title() for perm, value in permissions if value]
    if not perm_list:
        return "None"
    perm_str = ", ".join(perm_list)
    # Discord embed field value limit is 1024 characters
    return f"{perm_str[:1021]}..." if len(perm_str) > 1024 else perm_str


def format_guild_verification_level(level: discord.VerificationLevel) -> str:
    """Format verification level to readable string.

    Parameters
    ----------
    level : discord.VerificationLevel
        The verification level to format.

    Returns
    -------
    str
        Formatted verification level string.
    """
    verification_names = {
        discord.VerificationLevel.none: "None",
        discord.VerificationLevel.low: "Low",
        discord.VerificationLevel.medium: "Medium",
        discord.VerificationLevel.high: "High",
        discord.VerificationLevel.highest: "Highest",
    }
    return verification_names.get(level, str(level))


def format_guild_nsfw_level(guild: discord.Guild) -> str:
    """Format NSFW level to readable string.

    Parameters
    ----------
    guild : discord.Guild
        The guild to get NSFW level from.

    Returns
    -------
    str
        Formatted NSFW level string.
    """
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
    """Format content filter level to readable string.

    Parameters
    ----------
    level : discord.ContentFilter
        The content filter level to format.

    Returns
    -------
    str
        Formatted content filter string.
    """
    content_filter_names = {
        discord.ContentFilter.disabled: "Disabled",
        discord.ContentFilter.no_role: "No Role",
        discord.ContentFilter.all_members: "All Members",
    }
    return content_filter_names.get(level, str(level))


def format_guild_notifications(level: discord.NotificationLevel) -> str:
    """Format notification level to readable string.

    Parameters
    ----------
    level : discord.NotificationLevel
        The notification level to format.

    Returns
    -------
    str
        Formatted notification level string.
    """
    notification_names = {
        discord.NotificationLevel.all_messages: "All Messages",
        discord.NotificationLevel.only_mentions: "Only Mentions",
    }
    return notification_names.get(level, str(level))


def format_guild_premium_tier(tier: object) -> str:
    """Format premium tier to readable string.

    Parameters
    ----------
    tier : object
        The premium tier to format.

    Returns
    -------
    str
        Formatted premium tier string.
    """
    try:
        tier_value = int(tier)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return str(tier).replace("_", " ").title()
    else:
        return f"Tier {tier_value}" if tier_value > 0 else "None"


def format_invite_uses(invite: discord.Invite) -> str:
    """Format invite uses to readable string.

    Parameters
    ----------
    invite : discord.Invite
        The invite to format uses from.

    Returns
    -------
    str
        Formatted uses string.
    """
    if invite.max_uses:
        return f"{invite.uses}/{invite.max_uses}"
    return f"{invite.uses}/∞"


def format_invite_max_age(max_age: int | None) -> str:
    """Format invite max age to readable string.

    Parameters
    ----------
    max_age : int | None
        The max age in seconds to format.

    Returns
    -------
    str
        Formatted max age string.
    """
    if max_age and max_age > 0:
        days = max_age // 86400
        hours = (max_age % 86400) // 3600
        return f"{days}d {hours}h" if days > 0 else f"{hours}h"
    return "Never"


# ---- Invite ----


def extract_invite_code(invite_input: str) -> str:
    """Extract invite code from URL or return as-is.

    Parameters
    ----------
    invite_input : str
        The invite code or URL.

    Returns
    -------
    str
        The extracted invite code.
    """
    invite_input_lower = invite_input.lower()
    if "discord.gg/" in invite_input_lower:
        return invite_input.rsplit("discord.gg/", maxsplit=1)[-1].split("?")[0]
    if "discord.com/invite/" in invite_input_lower:
        return invite_input.rsplit("discord.com/invite/", maxsplit=1)[-1].split("?")[0]
    return invite_input


# ---- Guild ----


def count_guild_members(guild: discord.Guild) -> tuple[int, int]:
    """Count humans and bots in guild.

    Parameters
    ----------
    guild : discord.Guild
        The guild to count members from.

    Returns
    -------
    tuple[int, int]
        Tuple of (humans, bots) counts.
    """
    humans = 0
    bots = 0
    for member in guild.members:
        if member.bot:
            bots += 1
        else:
            humans += 1
    return humans, bots


async def count_guild_bans(guild: discord.Guild) -> int:
    """Count bans in guild.

    Parameters
    ----------
    guild : discord.Guild
        The guild to count bans from.

    Returns
    -------
    int
        Number of bans.
    """
    ban_count = 0
    async for __ in guild.bans(limit=BANS_LIMIT):
        ban_count += 1
    return ban_count


def build_guild_channel_counts(guild: discord.Guild) -> str:
    """Build channel counts text for guild.

    Parameters
    ----------
    guild : discord.Guild
        The guild to get channel counts from.

    Returns
    -------
    str
        Formatted channel counts string.
    """
    return (
        f"Text: {len(guild.text_channels)}, "
        f"Voice: {len(guild.voice_channels)}, "
        f"Forum: {len(guild.forums)}, "
        f"Stage: {len(guild.stage_channels)}, "
        f"Categories: {len(guild.categories)}"
    )


def build_guild_member_stats(
    guild: discord.Guild,
    humans: int,
    bots: int,
    ban_count: int,
) -> str:
    """Build member statistics text for guild.

    Parameters
    ----------
    guild : discord.Guild
        The guild to get member stats from.
    humans : int
        Number of human members.
    bots : int
        Number of bot members.
    ban_count : int
        Number of banned members.

    Returns
    -------
    str
        Formatted member statistics string.
    """
    total_members = guild.member_count or humans + bots
    member_stats = f"Total: {total_members} (Humans: {humans}, Bots: {bots})"
    max_presences = getattr(guild, "max_presences", None)
    if max_presences:
        member_stats += f" | Max Presences: {max_presences}"
    member_stats += f" | Banned: {ban_count}"
    return member_stats


def build_guild_special_channels(guild: discord.Guild) -> str:
    """Build special channels text for guild.

    Parameters
    ----------
    guild : discord.Guild
        The guild to get special channels from.

    Returns
    -------
    str
        Formatted special channels string.
    """
    special_channels: list[str] = []
    if guild.afk_channel:
        special_channels.append(
            f"AFK: {guild.afk_channel.mention} ({guild.afk_timeout // 60}m)",
        )
    if guild.system_channel:
        special_channels.append(f"System: {guild.system_channel.mention}")
    if guild.rules_channel:
        special_channels.append(f"Rules: {guild.rules_channel.mention}")
    if hasattr(guild, "public_updates_channel") and guild.public_updates_channel:
        special_channels.append(
            f"Public Updates: {guild.public_updates_channel.mention}",
        )
    if hasattr(guild, "safety_alerts_channel") and guild.safety_alerts_channel:
        special_channels.append(f"Safety: {guild.safety_alerts_channel.mention}")
    if hasattr(guild, "widget_channel") and guild.widget_channel:
        special_channels.append(f"Widget: {guild.widget_channel.mention}")
    return ", ".join(special_channels) if special_channels else "None"


def add_guild_title_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add title and description section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    guild : discord.Guild
        The guild to get information from.
    """
    description = guild.description or "No description available."
    title_content = f"# {guild.name}\n\n{description}"

    # Add title section with icon thumbnail as accessory if available
    if guild.icon:
        container.add_item(
            discord.ui.Section[discord.ui.LayoutView](
                discord.ui.TextDisplay[discord.ui.LayoutView](title_content),
                accessory=discord.ui.Thumbnail[discord.ui.LayoutView](
                    media=guild.icon.url,
                ),
            ),
        )
    else:
        container.add_item(
            discord.ui.TextDisplay(title_content),
        )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_basic_info_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
    tier_text: str,
) -> None:
    """Add basic information section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    guild : discord.Guild
        The guild to get information from.
    tier_text : str
        Formatted premium tier text.
    """
    owner_text = str(guild.owner.mention) if guild.owner else "Unknown"
    container.add_item(
        discord.ui.TextDisplay(
            f"### Basic Information\n"
            f"👑 **Owner:** {owner_text} • "
            f"🔗 **Vanity URL:** {guild.vanity_url_code or 'None'} • "
            f"💎 **Premium Tier:** {tier_text}\n"
            f"⭐ **Boosts:** {guild.premium_subscription_count}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_security_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    verification_text: str,
    mfa_text: str,
    nsfw_text: str,
    content_filter_text: str,
    notification_text: str,
) -> None:
    """Add security and settings section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    verification_text : str
        Formatted verification level text.
    mfa_text : str
        Formatted MFA level text.
    nsfw_text : str
        Formatted NSFW level text.
    content_filter_text : str
        Formatted content filter text.
    notification_text : str
        Formatted notification level text.
    """
    container.add_item(
        discord.ui.TextDisplay(
            f"### Security & Settings\n"
            f"🔒 **Verification:** {verification_text} • "
            f"🛡️ **MFA Level:** {mfa_text} • "
            f"🔞 **NSFW Level:** {nsfw_text}\n"
            f"🚫 **Content Filter:** {content_filter_text} • "
            f"🔔 **Notifications:** {notification_text}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_channels_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel_counts: str,
    special_channels_text: str,
) -> None:
    """Add channels section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    channel_counts : str
        Formatted channel counts text.
    special_channels_text : str
        Formatted special channels text.
    """
    container.add_item(
        discord.ui.TextDisplay(
            f"### Channels\n"
            f"📝 **Channels:** {channel_counts}\n"
            f"📍 **Special Channels:** {special_channels_text}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_resources_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add resources section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    guild : discord.Guild
        The guild to get information from.
    """
    container.add_item(
        discord.ui.TextDisplay(
            f"### Resources\n"
            f"😀 **Emojis:** {len(guild.emojis)}/{2 * guild.emoji_limit} • "
            f"🎨 **Stickers:** {len(guild.stickers)}/{guild.sticker_limit} • "
            f"🎭 **Roles:** {len(guild.roles)}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_members_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    member_stats: str,
) -> None:
    """Add members section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    member_stats : str
        Formatted member statistics text.
    """
    container.add_item(
        discord.ui.TextDisplay(
            f"### Members\n{member_stats}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_footer_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add footer section to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add section to.
    guild : discord.Guild
        The guild to get information from.
    """
    footer_text = (
        f"🆔 **ID:** `{guild.id}` • "
        f"📅 **Created:** {format_date_long(guild.created_at)}"
    )
    container.add_item(
        discord.ui.TextDisplay(footer_text),
    )


def add_guild_media(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add icon and banner media to guild container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add media to.
    guild : discord.Guild
        The guild to get media from.
    """
    if guild.banner:
        container.add_item(
            discord.ui.MediaGallery(
                discord.MediaGalleryItem(guild.banner.url),
            ),
        )


# ---- Invite sections ----


def add_invite_statistics(
    container: discord.ui.Container[discord.ui.LayoutView],
    invite: discord.Invite,
) -> None:
    """Add invite statistics section to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add statistics to.
    invite : discord.Invite
        The invite to get statistics from.
    """
    if (
        hasattr(invite, "approximate_member_count")
        and invite.approximate_member_count is not None
    ):
        container.add_item(
            discord.ui.TextDisplay(
                f"### Statistics\n"
                f"👥 **Approx. Members:** ~{invite.approximate_member_count:,}",
            ),
        )
        if (
            hasattr(invite, "approximate_presence_count")
            and invite.approximate_presence_count is not None
        ):
            container.add_item(
                discord.ui.TextDisplay(
                    f"🟢 **Approx. Online:** ~{invite.approximate_presence_count:,}",
                ),
            )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_invite_target_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    invite: discord.Invite,
) -> None:
    """Add invite target information section to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add target info to.
    invite : discord.Invite
        The invite to get target info from.
    """
    if hasattr(invite, "target_type") and invite.target_type:
        target_type_name = str(invite.target_type).replace("_", " ").title()
        target_parts: list[str] = [f"**Target Type:** {target_type_name}"]
        if hasattr(invite, "target_user") and invite.target_user:
            target_parts.append(f"**Target User:** {invite.target_user.mention}")
        if hasattr(invite, "target_application") and invite.target_application:
            app_name = getattr(invite.target_application, "name", "Unknown Application")
            target_parts.append(f"**Target Application:** {app_name}")

        container.add_item(
            discord.ui.TextDisplay(
                f"### Target Information\n{' • '.join(target_parts)}",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_invite_scheduled_event(
    container: discord.ui.Container[discord.ui.LayoutView],
    invite: discord.Invite,
) -> None:
    """Add invite scheduled event section to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add scheduled event info to.
    invite : discord.Invite
        The invite to get scheduled event info from.
    """
    if hasattr(invite, "scheduled_event") and invite.scheduled_event:
        container.add_item(
            discord.ui.TextDisplay(
                f"### Scheduled Event\n📅 **Event:** {invite.scheduled_event.name}",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
    elif hasattr(invite, "scheduled_event_id") and invite.scheduled_event_id:
        container.add_item(
            discord.ui.TextDisplay(
                f"### Scheduled Event\n🆔 **Event ID:** `{invite.scheduled_event_id}`",
            ),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


# ---- Channel ----


def add_text_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.TextChannel,
) -> None:
    """Add TextChannel-specific information to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add information to.
    channel : discord.TextChannel
        The text channel to get information from.
    """
    parts: list[str] = [
        f"**Slowmode:** {channel.slowmode_delay}s"
        if channel.slowmode_delay > 0
        else "**Slowmode:** None",
    ]
    if hasattr(channel, "default_auto_archive_duration"):
        duration = channel.default_auto_archive_duration
        parts.append(
            f"**Default Archive Duration:** {duration // 60}h"
            if duration
            else "**Default Archive Duration:** None",
        )
    if hasattr(channel, "threads"):
        parts.append(f"**Active Threads:** {len(channel.threads)}")

    if parts:
        container.add_item(
            discord.ui.TextDisplay(f"### Text Channel Settings\n{' • '.join(parts)}"),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_voice_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.VoiceChannel,
) -> None:
    """Add VoiceChannel-specific information to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add information to.
    channel : discord.VoiceChannel
        The voice channel to get information from.
    """
    parts: list[str] = [
        f"**Bitrate:** {channel.bitrate // 1000}kbps",
        f"**User Limit:** {channel.user_limit or 'Unlimited'}",
    ]
    if hasattr(channel, "rtc_region") and channel.rtc_region:
        rtc_region = channel.rtc_region
        region_value = str(getattr(rtc_region, "name", rtc_region))
        parts.append(f"**RTC Region:** {region_value}")

    if parts:
        container.add_item(
            discord.ui.TextDisplay(f"### Voice Channel Settings\n{' • '.join(parts)}"),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_stage_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.StageChannel,
) -> None:
    """Add StageChannel-specific information to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add information to.
    channel : discord.StageChannel
        The stage channel to get information from.
    """
    parts: list[str] = [
        f"**Bitrate:** {channel.bitrate // 1000}kbps",
        f"**User Limit:** {channel.user_limit or 'Unlimited'}",
    ]
    if hasattr(channel, "topic") and channel.topic:
        topic = channel.topic
        parts.append(f"**Topic:** {topic[:100]}{'...' if len(topic) > 100 else ''}")
    if hasattr(channel, "instance"):
        parts.append(
            f"**Active Instance:** {format_bool(channel.instance is not None)}",
        )

    if parts:
        container.add_item(
            discord.ui.TextDisplay(f"### Stage Channel Settings\n{' • '.join(parts)}"),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_forum_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.ForumChannel,
) -> None:
    """Add ForumChannel-specific information to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add information to.
    channel : discord.ForumChannel
        The forum channel to get information from.
    """
    parts: list[str] = [
        f"**Available Tags:** {len(channel.available_tags)}",
        f"**Default Layout:** {str(channel.default_layout).replace('_', ' ').title()}",
    ]
    if hasattr(channel, "default_auto_archive_duration"):
        duration = channel.default_auto_archive_duration
        parts.append(
            f"**Default Archive Duration:** {duration // 60}h"
            if duration
            else "**Default Archive Duration:** None",
        )
    if hasattr(channel, "threads"):
        parts.append(f"**Active Threads:** {len(channel.threads)}")

    if parts:
        container.add_item(
            discord.ui.TextDisplay(f"### Forum Channel Settings\n{' • '.join(parts)}"),
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_category_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.CategoryChannel,
) -> None:
    """Add CategoryChannel-specific information to container.

    Parameters
    ----------
    container : discord.ui.Container[discord.ui.LayoutView]
        The container to add information to.
    channel : discord.CategoryChannel
        The category channel to get information from.
    """
    parts: list[str] = [
        f"**Text Channels:** {len(channel.text_channels)}",
        f"**Voice Channels:** {len(channel.voice_channels)}",
        f"**Stage Channels:** {len(channel.stage_channels)}",
        f"**Forum Channels:** {len(channel.forums)}",
        f"**Total Channels:** {len(channel.channels)}",
    ]

    container.add_item(
        discord.ui.TextDisplay(f"### Category Channels\n{' • '.join(parts)}"),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


# ---- Role ----


def get_role_type_info(role: discord.Role) -> list[tuple[str, bool]]:
    """Get role type information.

    Parameters
    ----------
    role : discord.Role
        The role to get type information from.

    Returns
    -------
    list[tuple[str, bool]]
        List of tuples containing role type name and boolean value.
    """
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
    """Get role tags information.

    Parameters
    ----------
    role : discord.Role
        The role to get tags information from.

    Returns
    -------
    list[str] | None
        List of tag information strings, or None if no tags.
    """
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
    """Get role flags information.

    Parameters
    ----------
    role : discord.Role
        The role to get flags information from.

    Returns
    -------
    list[str] | None
        List of flag names, or None if no flags.
    """
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


# ---- User ----


def get_user_banner(user: discord.User) -> str | None:
    """Get the banner URL from a user object.

    Parameters
    ----------
    user : discord.User
        The user to get the banner from.

    Returns
    -------
    str | None
        The banner URL if available, None otherwise.
    """
    banner = getattr(user, "banner", None)
    return getattr(banner, "url", None)


async def get_member_banner(member: discord.Member, bot: Tux) -> str | None:
    """Get the banner URL from a member's user object.

    Fetches the user to ensure banner data is included.
    This is necessary because cached users may not have banner information.

    Parameters
    ----------
    member : discord.Member
        The member to get the banner from.
    bot : Tux
        The bot instance to use for fetching.

    Returns
    -------
    str | None
        The banner URL if available, None otherwise.
    """
    # Fetch user to get banner data (required for discord.py v2.0+)
    # Members don't have banner data in cache, so we must fetch
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


# ---- Misc ----


def chunks[T](it: Iterator[T], size: int) -> Generator[list[T]]:
    """Split an iterator into chunks of a specified size.

    Parameters
    ----------
    it : Iterator[T]
        The input iterator to be split into chunks.
    size : int
        The size of each chunk.

    Yields
    ------
    list[T]
        A list containing a chunk of elements from the input iterator. The last
        list may contain fewer elements if there are not enough remaining to fill
        a complete chunk.
    """
    chunk: list[T] = []
    for item in it:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
