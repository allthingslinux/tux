"""View builders for info command displays."""

import discord

from tux.core.bot import Tux

from .helpers import (
    add_category_channel_info,
    add_forum_channel_info,
    add_guild_basic_info_section,
    add_guild_channels_section,
    add_guild_footer_section,
    add_guild_media,
    add_guild_members_section,
    add_guild_resources_section,
    add_guild_security_section,
    add_guild_title_section,
    add_invite_scheduled_event,
    add_invite_statistics,
    add_invite_target_info,
    add_stage_channel_info,
    add_text_channel_info,
    add_voice_channel_info,
    build_guild_channel_counts,
    build_guild_member_stats,
    build_guild_special_channels,
    count_guild_bans,
    count_guild_members,
    format_bool,
    format_date_long,
    format_datetime,
    format_guild_content_filter,
    format_guild_notifications,
    format_guild_nsfw_level,
    format_guild_premium_tier,
    format_guild_verification_level,
    format_invite_max_age,
    format_invite_uses,
    format_permissions,
    get_member_banner,
    get_role_flags_info,
    get_role_tags_info,
    get_role_type_info,
)

ContainerT = discord.ui.Container[discord.ui.LayoutView]


def _create_info_view(
    accent_color: int = 0x5865F2,
) -> tuple[discord.ui.LayoutView, ContainerT]:
    """Create a LayoutView and Container, add container to view, return both."""
    view = discord.ui.LayoutView(timeout=None)
    container = ContainerT(accent_color=accent_color)
    view.add_item(container)
    return view, container


def _add_section(
    container: ContainerT,
    heading: str,
    content: str,
    add_sep: bool = True,
) -> None:
    """Append a TextDisplay section and optionally a small Separator."""
    container.add_item(discord.ui.TextDisplay(f"### {heading}\n{content}"))
    if add_sep:
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))


def _add_footer(container: ContainerT, id_str: str, created_str: str) -> None:
    """Append the shared ID • Created footer TextDisplay."""
    container.add_item(
        discord.ui.TextDisplay(f"🆔 **ID:** {id_str} • 📅 **Created:** {created_str}"),
    )


async def build_guild_view(guild: discord.Guild) -> discord.ui.LayoutView:
    """Build a Components V2 view for guild information.

    Parameters
    ----------
    guild : discord.Guild
        The guild to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    # Gather data
    humans, bots = await count_guild_members(guild)
    ban_count = await count_guild_bans(guild)

    # Format settings
    verification_text = format_guild_verification_level(guild.verification_level)
    mfa_text = "Required" if guild.mfa_level.value == 1 else "None"
    nsfw_text = format_guild_nsfw_level(guild)
    content_filter_text = format_guild_content_filter(guild.explicit_content_filter)
    notification_text = format_guild_notifications(guild.default_notifications)
    tier_text = format_guild_premium_tier(guild.premium_tier)

    # Build text sections
    channel_counts = build_guild_channel_counts(guild)
    member_stats = build_guild_member_stats(guild, humans, bots, ban_count)
    special_channels_text = build_guild_special_channels(guild)

    view, container = _create_info_view()

    add_guild_title_section(container, guild)
    add_guild_basic_info_section(container, guild, tier_text)
    add_guild_security_section(
        container,
        verification_text,
        mfa_text,
        nsfw_text,
        content_filter_text,
        notification_text,
    )
    add_guild_channels_section(container, channel_counts, special_channels_text)
    add_guild_resources_section(container, guild)
    add_guild_members_section(container, member_stats)
    add_guild_footer_section(container, guild)
    add_guild_media(container, guild)

    return view


async def build_member_view(member: discord.Member, bot: Tux) -> discord.ui.LayoutView:
    """Build a Components V2 view for member information.

    Parameters
    ----------
    member : discord.Member
        The member to display information about.
    bot : Tux
        The bot instance for fetching user data.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    banner_url = await get_member_banner(member, bot)  # noqa: F841  # pyright: ignore[reportUnusedVariable]

    # Build username display
    global_name = getattr(member, "global_name", None)
    username_display = (
        f"{member.name} ({global_name})"
        if global_name and global_name != member.name
        else member.name
    )

    view, container = _create_info_view()

    container.add_item(
        discord.ui.TextDisplay(
            f"# {member.display_name}\n\nHere is some information about the member.",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    status_text = ""
    if hasattr(member, "status") and member.status:
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫",
            discord.Status.invisible: "⚫",
        }.get(member.status, "⚫")
        status_text = f" • **Status:** {status_emoji} {str(member.status).title()}"

    _add_section(
        container,
        "Basic Information",
        f"👤 **Username:** `{username_display}` • "
        f"🆔 **ID:** `{member.id}` • "
        f"🤖 **Bot:** {format_bool(member.bot)}{status_text}",
    )

    # Additional flags
    flags_parts: list[str] = []
    if hasattr(member, "system") and member.system:
        flags_parts.append(f"**System:** {format_bool(member.system)}")
    if hasattr(member, "pending") and member.pending:
        flags_parts.append(f"**Pending:** {format_bool(member.pending)}")
    if flags_parts:
        _add_section(container, "Flags", " • ".join(flags_parts))

    dates_parts: list[str] = []
    if hasattr(member, "timed_out_until") and member.timed_out_until:
        dates_parts.append(
            f"**Timed Out Until:** {format_datetime(member.timed_out_until)}",
        )
    if hasattr(member, "premium_since") and member.premium_since:
        dates_parts.append(
            f"**Premium Since:** {format_datetime(member.premium_since)}",
        )
    dates_parts.extend(
        [
            f"**Joined:** {format_datetime(member.joined_at)}",
            f"**Registered:** {format_datetime(member.created_at)}",
        ],
    )
    _add_section(container, "Dates", " • ".join(f"📅 {part}" for part in dates_parts))

    roles_list = [role.mention for role in member.roles[1:]]
    roles_display = ", ".join(roles_list) if roles_list else "No roles"

    # Truncate if too long (Discord limit is 4000 chars, reserve ~100 for heading/formatting)
    max_roles_length = 3900
    if len(roles_display) > max_roles_length:
        # Find the last complete role mention that fits
        truncated = roles_display[:max_roles_length]
        last_comma = truncated.rfind(", ")
        if last_comma > 0:
            truncated = truncated[:last_comma]
            # Count how many roles are in the truncated string
            roles_included = truncated.count(", ") + 1
            remaining = len(roles_list) - roles_included
            roles_display = f"{truncated} (+{remaining} more roles)"
        else:
            roles_display = f"{truncated}..."

    if member.top_role and member.top_role != member.guild.default_role:
        _add_section(
            container,
            "Roles",
            f"👑 **Top Role:** {member.top_role.mention}\n"
            f"🎭 **All Roles:** {roles_display}",
        )
    else:
        _add_section(container, "Roles", f"🎭 **All Roles:** {roles_display}")

    # TODO: Fix avatar and banner display in MediaGallery
    # The current implementation may have layout/positioning issues
    # Consider using Thumbnail as Section accessory or alternative layout approach
    # # Add avatar and banner to MediaGallery
    # gallery_items = [discord.MediaGalleryItem(member.display_avatar.url)]
    # if banner_url:
    #     gallery_items.append(discord.MediaGalleryItem(banner_url))
    # container.add_item(discord.ui.MediaGallery(*gallery_items))

    return view


def build_user_view(user: discord.User) -> discord.ui.LayoutView:
    """Build a Components V2 view for user information.

    Parameters
    ----------
    user : discord.User
        The user to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    global_name = getattr(user, "global_name", None)
    username_display = (
        f"{user.name} ({global_name})"
        if global_name and global_name != user.name
        else user.name
    )

    view, container = _create_info_view()

    container.add_item(
        discord.ui.TextDisplay(
            f"# {user.display_name}\n\nHere is some information about the user.",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    _add_section(
        container,
        "Basic Information",
        f"👤 **Username:** `{username_display}` • "
        f"🆔 **ID:** `{user.id}` • "
        f"🤖 **Bot:** {format_bool(user.bot)}",
    )

    if hasattr(user, "system") and user.system:
        _add_section(container, "Flags", f"🛡️ **System:** {format_bool(user.system)}")

    if hasattr(user, "accent_color") and user.accent_color:
        _add_section(
            container,
            "Appearance",
            f"🎨 **Accent Color:** `#{user.accent_color.value:06x}`",
        )

    _add_section(
        container,
        "Dates",
        f"📅 **Registered:** {format_datetime(user.created_at)}",
        add_sep=False,
    )

    # TODO: Fix avatar and banner display in MediaGallery
    # The current implementation may have layout/positioning issues
    # Consider using Thumbnail as Section accessory or alternative layout approach
    # # Add avatar and banner to MediaGallery
    # gallery_items = [discord.MediaGalleryItem(user.display_avatar.url)]
    # if banner_url := get_user_banner(user):
    #     gallery_items.append(discord.MediaGalleryItem(banner_url))
    # container.add_item(discord.ui.MediaGallery(*gallery_items))

    return view


def build_channel_view(
    channel: discord.abc.GuildChannel,
) -> discord.ui.LayoutView:
    """Build a Components V2 view for channel information.

    Parameters
    ----------
    channel : discord.abc.GuildChannel
        The channel to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    channel_type = channel.__class__.__name__
    description = getattr(channel, "topic", None) or "No topic available."

    view, container = _create_info_view()

    container.add_item(
        discord.ui.TextDisplay(f"# #{channel.name}\n\n{description}"),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    category_name = channel.category.name if channel.category else "None"
    _add_section(
        container,
        "Basic Information",
        f"📋 **Type:** `{channel_type}` • "
        f"📍 **Position:** `{channel.position}` • "
        f"📁 **Category:** {category_name}",
    )

    if isinstance(
        channel,
        (
            discord.TextChannel,
            discord.VoiceChannel,
            discord.StageChannel,
            discord.ForumChannel,
            discord.CategoryChannel,
        ),
    ) and hasattr(channel, "nsfw"):
        _add_section(container, "Settings", f"🔞 **NSFW:** {format_bool(channel.nsfw)}")

    if isinstance(channel, discord.TextChannel):
        add_text_channel_info(container, channel)
    elif isinstance(channel, discord.VoiceChannel):
        add_voice_channel_info(container, channel)
    elif isinstance(channel, discord.StageChannel):
        add_stage_channel_info(container, channel)
    elif isinstance(channel, discord.ForumChannel):
        add_forum_channel_info(container, channel)
    elif isinstance(channel, discord.CategoryChannel):
        add_category_channel_info(container, channel)

    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
    _add_footer(
        container,
        f"`{channel.id}`",
        format_date_long(channel.created_at),
    )

    return view


def build_role_view(role: discord.Role) -> discord.ui.LayoutView:
    """Build a Components V2 view for role information.

    Parameters
    ----------
    role : discord.Role
        The role to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    # Build description
    description = "Here is some information about the role."
    if hasattr(role, "unicode_emoji") and role.unicode_emoji:
        description = f"{role.unicode_emoji} {description}"
    elif hasattr(role, "display_icon") and role.display_icon:
        description = f"{description} (Has custom icon)"

    accent_color = (
        role.color.value if role.color != discord.Color.default() else 0x5865F2
    )
    view, container = _create_info_view(accent_color)

    container.add_item(
        discord.ui.TextDisplay(f"# {role.name}\n\n{description}"),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    color_text = (
        f"#{role.color.value:06x}"
        if role.color != discord.Color.default()
        else "Default"
    )
    _add_section(
        container,
        "Basic Information",
        f"🎨 **Color:** `{color_text}` • "
        f"📍 **Position:** `{role.position}` • "
        f"👥 **Members:** `{len(role.members)}`",
    )

    color_parts: list[str] = []
    if (
        hasattr(role, "secondary_color")
        and role.secondary_color
        and role.secondary_color != discord.Color.default()
    ):
        color_parts.append(f"**Secondary Color:** `#{role.secondary_color.value:06x}`")
    if (
        hasattr(role, "tertiary_color")
        and role.tertiary_color
        and role.tertiary_color != discord.Color.default()
    ):
        color_parts.append(f"**Tertiary Color:** `#{role.tertiary_color.value:06x}`")

    if color_parts:
        _add_section(container, "Colors", "🎨 " + " • ".join(color_parts))

    _add_section(
        container,
        "Properties",
        f"💬 **Mentionable:** {format_bool(role.mentionable)} • "
        f"⬆️ **Hoisted:** {format_bool(role.hoist)} • "
        f"🤖 **Managed:** {format_bool(role.managed)}",
    )

    if role_type_info := get_role_type_info(role):
        type_parts = [
            f"**{name}:** {format_bool(value)}" for name, value in role_type_info
        ]
        _add_section(container, "Role Type", " • ".join(type_parts))

    if tags_info := get_role_tags_info(role):
        _add_section(
            container,
            "Role Tags",
            "\n".join(f"🏷️ {tag}" for tag in tags_info),
        )

    if flags_list := get_role_flags_info(role):
        _add_section(container, "Flags", f"🚩 {', '.join(flags_list)}")

    _add_section(
        container,
        "Permissions",
        format_permissions(role.permissions),
    )

    _add_footer(container, f"`{role.id}`", format_date_long(role.created_at))

    return view


def build_emoji_view(emoji: discord.Emoji) -> discord.ui.LayoutView:
    """Build a Components V2 view for emoji information.

    Parameters
    ----------
    emoji : discord.Emoji
        The emoji to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    view, container = _create_info_view()

    container.add_item(
        discord.ui.TextDisplay(
            f"# {emoji.name}\n\nHere is some information about the emoji.\n\n{emoji}",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    _add_section(
        container,
        "Basic Information",
        f"🎬 **Animated:** {format_bool(emoji.animated)} • "
        f"🤖 **Managed:** {format_bool(emoji.managed)} • "
        f"✅ **Available:** {format_bool(emoji.available)}\n"
        f"🔤 **Requires Colons:** {format_bool(emoji.require_colons)}",
    )

    additional_parts: list[str] = []
    if hasattr(emoji, "is_application_owned") and (
        is_app_owned := emoji.is_application_owned()
    ):
        additional_parts.append(f"**Application Owned:** {format_bool(is_app_owned)}")
    if hasattr(emoji, "is_usable"):
        is_usable = emoji.is_usable()
        additional_parts.append(f"**Usable:** {format_bool(is_usable)}")

    if additional_parts:
        _add_section(container, "Additional Information", " • ".join(additional_parts))

    info_parts: list[str] = []
    if emoji.guild:
        info_parts.append(f"**Guild:** {emoji.guild.name}")
    if emoji.user:
        info_parts.append(f"**Created By:** {emoji.user.mention}")

    if info_parts:
        _add_section(container, "Details", " • ".join(info_parts))

    if emoji.roles:
        roles_display = ", ".join(role.mention for role in emoji.roles[:10])
        if len(emoji.roles) > 10:
            roles_display += f" (+{len(emoji.roles) - 10} more)"
        _add_section(container, "Role Restrictions", f"🎭 {roles_display}")

    _add_footer(container, f"`{emoji.id}`", format_date_long(emoji.created_at))

    # Add emoji as MediaGallery for better display
    container.add_item(
        discord.ui.MediaGallery(
            discord.MediaGalleryItem(emoji.url),
        ),
    )

    return view


def build_invite_view(invite: discord.Invite) -> discord.ui.LayoutView:
    """Build a Components V2 view for invite information.

    Parameters
    ----------
    invite : discord.Invite
        The invite to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    guild_name = "Unknown Server"
    if invite.guild:
        guild_name = getattr(invite.guild, "name", "Unknown Server")

    uses_text = format_invite_uses(invite)
    max_age_text = format_invite_max_age(invite.max_age)

    view, container = _create_info_view()

    container.add_item(
        discord.ui.TextDisplay(
            f"# Invite to {guild_name}\n\n**Code:** `{invite.code}`",
        ),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    channel_mention = (
        getattr(invite.channel, "mention", "Unknown") if invite.channel else "Unknown"
    )
    inviter_mention = invite.inviter.mention if invite.inviter else "Unknown"
    invite_type = (
        str(invite.type).replace("_", " ").title()
        if hasattr(invite, "type")
        else "Unknown"
    )

    _add_section(
        container,
        "Basic Information",
        f"🏠 **Guild:** {guild_name} • "
        f"📺 **Channel:** {channel_mention} • "
        f"👤 **Inviter:** {inviter_mention}\n"
        f"📋 **Type:** {invite_type}",
    )

    expires_text = (
        discord.utils.format_dt(invite.expires_at, "R")
        if invite.expires_at
        else "Never"
    )
    _add_section(
        container,
        "Usage & Settings",
        f"🔢 **Uses:** {uses_text} • "
        f"⏰ **Max Age:** {max_age_text} • "
        f"⏳ **Expires:** {expires_text}\n"
        f"⏱️ **Temporary:** {format_bool(invite.temporary or False)} • "
        f"🚫 **Revoked:** {format_bool(invite.revoked or False)}",
    )

    add_invite_statistics(container, invite)

    add_invite_target_info(container, invite)
    add_invite_scheduled_event(container, invite)

    footer_parts = [f"🆔 **ID:** `{invite.id}`"]
    created_str = format_date_long(invite.created_at)
    if created_str != "Unknown":
        footer_parts.append(f"📅 **Created:** {created_str}")
    container.add_item(
        discord.ui.TextDisplay(" | ".join(footer_parts)),
    )

    if hasattr(invite, "url") and invite.url:
        container.add_item(
            discord.ui.TextDisplay(
                f"### Link\n🔗 [Click here to join]({invite.url})",
            ),
        )

    return view


def build_thread_view(thread: discord.Thread) -> discord.ui.LayoutView:
    """Build a Components V2 view for thread information.

    Parameters
    ----------
    thread : discord.Thread
        The thread to display information about.

    Returns
    -------
    discord.ui.LayoutView
        The built view.
    """
    view, container = _create_info_view()

    topic = getattr(thread, "topic", None) or "No topic available."

    container.add_item(
        discord.ui.TextDisplay(f"# Thread: {thread.name}\n\n{topic}"),
    )
    container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

    owner_mention = thread.owner.mention if thread.owner else "Unknown"
    parent_mention = thread.parent.mention if thread.parent else "None"
    _add_section(
        container,
        "Basic Information",
        f"📋 **Type:** `{thread.__class__.__name__}` • "
        f"👤 **Owner:** {owner_mention} • "
        f"📁 **Parent:** {parent_mention}",
    )

    _add_section(
        container,
        "Status",
        f"📦 **Archived:** {format_bool(thread.archived)} • "
        f"🔒 **Locked:** {format_bool(thread.locked)} • "
        f"💬 **Message Count:** {thread.message_count}",
    )

    _add_footer(container, f"`{thread.id}`", format_date_long(thread.created_at))

    return view
