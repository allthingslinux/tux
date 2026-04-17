"""Guild and invite embed section builders for info commands."""

import discord

from tux.shared.constants import BANS_LIMIT

from .formatting import format_date_long


def count_guild_members(guild: discord.Guild) -> tuple[int, int]:
    """Count humans and bots in guild."""
    humans = 0
    bots = 0
    for member in guild.members:
        if member.bot:
            bots += 1
        else:
            humans += 1
    return humans, bots


async def count_guild_bans(guild: discord.Guild) -> int:
    """Count bans in guild."""
    ban_count = 0
    async for __ in guild.bans(limit=BANS_LIMIT):
        ban_count += 1
    return ban_count


def build_guild_channel_counts(guild: discord.Guild) -> str:
    """Build channel counts text for guild."""
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
    """Build member statistics text for guild."""
    total_members = guild.member_count or humans + bots
    member_stats = f"Total: {total_members} (Humans: {humans}, Bots: {bots})"
    max_presences = getattr(guild, "max_presences", None)
    if max_presences:
        member_stats += f" | Max Presences: {max_presences}"
    member_stats += f" | Banned: {ban_count}"
    return member_stats


def build_guild_special_channels(guild: discord.Guild) -> str:
    """Build special channels text for guild."""
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
    """Add title and description section to guild container."""
    description = guild.description or "No description available."
    title_content = f"# {guild.name}\n\n{description}"
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
        container.add_item(discord.ui.TextDisplay(title_content))
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_basic_info_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
    tier_text: str,
) -> None:
    """Add basic information section to guild container."""
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
    """Add security and settings section to guild container."""
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
    """Add channels section to guild container."""
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
    """Add resources section to guild container."""
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
    """Add members section to guild container."""
    container.add_item(discord.ui.TextDisplay(f"### Members\n{member_stats}"))
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def add_guild_footer_section(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add footer section to guild container."""
    container.add_item(
        discord.ui.TextDisplay(
            f"🆔 **ID:** `{guild.id}` • 📅 **Created:** {format_date_long(guild.created_at)}",
        ),
    )


def add_guild_media(
    container: discord.ui.Container[discord.ui.LayoutView],
    guild: discord.Guild,
) -> None:
    """Add icon and banner media to guild container."""
    if guild.banner:
        container.add_item(
            discord.ui.MediaGallery(discord.MediaGalleryItem(guild.banner.url)),
        )


def add_invite_statistics(
    container: discord.ui.Container[discord.ui.LayoutView],
    invite: discord.Invite,
) -> None:
    """Add invite statistics section to container."""
    if (
        hasattr(invite, "approximate_member_count")
        and invite.approximate_member_count is not None
    ):
        container.add_item(
            discord.ui.TextDisplay(
                f"### Statistics\n👥 **Approx. Members:** ~{invite.approximate_member_count:,}",
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
    """Add invite target information section to container."""
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
    """Add invite scheduled event section to container."""
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
