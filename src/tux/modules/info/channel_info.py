"""Channel-specific embed builders for info commands."""

import discord

from .formatting import format_bool


def add_text_channel_info(
    container: discord.ui.Container[discord.ui.LayoutView],
    channel: discord.TextChannel,
) -> None:
    """Add TextChannel-specific information to container."""
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
    """Add VoiceChannel-specific information to container."""
    parts: list[str] = [
        f"**Bitrate:** {channel.bitrate // 1000}kbps",
        f"**User Limit:** {channel.user_limit or 'Unlimited'}",
    ]
    if hasattr(channel, "rtc_region") and channel.rtc_region:
        region_value = str(getattr(channel.rtc_region, "name", channel.rtc_region))
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
    """Add StageChannel-specific information to container."""
    parts: list[str] = [
        f"**Bitrate:** {channel.bitrate // 1000}kbps",
        f"**User Limit:** {channel.user_limit or 'Unlimited'}",
    ]
    if hasattr(channel, "topic") and channel.topic:
        parts.append(
            f"**Topic:** {channel.topic[:100]}{'...' if len(channel.topic) > 100 else ''}",
        )
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
    """Add ForumChannel-specific information to container."""
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
    """Add CategoryChannel-specific information to container."""
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
