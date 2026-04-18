"""Helper utilities for info commands — re-export facade.

Actual implementations live in focused sibling modules:
- formatting.py: Discord object formatting, invite parsing, iterator utilities
- guild_info.py: Guild/invite embed section builders
- channel_info.py: Channel-specific embed builders
- role_user_info.py: Role and user helpers
"""

from .channel_info import (
    add_category_channel_info,
    add_forum_channel_info,
    add_stage_channel_info,
    add_text_channel_info,
    add_voice_channel_info,
)
from .formatting import (
    chunks,
    extract_invite_code,
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
)
from .guild_info import (
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
    build_guild_channel_counts,
    build_guild_member_stats,
    build_guild_special_channels,
    count_guild_bans,
    count_guild_members,
)
from .role_user_info import (
    get_member_banner,
    get_role_flags_info,
    get_role_tags_info,
    get_role_type_info,
    get_user_banner,
)

__all__ = [
    "add_category_channel_info",
    "add_forum_channel_info",
    "add_guild_basic_info_section",
    "add_guild_channels_section",
    "add_guild_footer_section",
    "add_guild_media",
    "add_guild_members_section",
    "add_guild_resources_section",
    "add_guild_security_section",
    "add_guild_title_section",
    "add_invite_scheduled_event",
    "add_invite_statistics",
    "add_invite_target_info",
    "add_stage_channel_info",
    "add_text_channel_info",
    "add_voice_channel_info",
    "build_guild_channel_counts",
    "build_guild_member_stats",
    "build_guild_special_channels",
    "chunks",
    "count_guild_bans",
    "count_guild_members",
    "extract_invite_code",
    "format_bool",
    "format_date_long",
    "format_datetime",
    "format_guild_content_filter",
    "format_guild_notifications",
    "format_guild_nsfw_level",
    "format_guild_premium_tier",
    "format_guild_verification_level",
    "format_invite_max_age",
    "format_invite_uses",
    "format_permissions",
    "get_member_banner",
    "get_role_flags_info",
    "get_role_tags_info",
    "get_role_type_info",
    "get_user_banner",
]
