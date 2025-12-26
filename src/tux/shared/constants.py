"""
Shared Constants for Tux Bot.

This module contains all application-wide constants and configuration values
used throughout the Tux Discord bot, including embed colors, icons, limits,
and API endpoints.
"""

from typing import Final

import discord

__all__ = [
    "ACTION_ROW_MAX_ITEMS",
    "ADD_BOOKMARK",
    "AFK_ALLOWED_MENTIONS",
    "AFK_PREFIX",
    "AFK_REASON_MAX_LENGTH",
    "AFK_SLEEPING_EMOJI",
    "ARCH_WIKI_API_URL",
    "ARCH_WIKI_BASE_URL",
    "BANS_LIMIT",
    "CONFIG_COLOR_BLURPLE",
    "CONFIG_COLOR_GREEN",
    "CONFIG_COLOR_RED",
    "CONFIG_COLOR_YELLOW",
    "CONFIG_COMMANDS_PER_PAGE",
    "CONFIG_DASHBOARD_TIMEOUT",
    "CONFIG_LOGS_PER_PAGE",
    "CONFIG_RANKS_PER_PAGE",
    "CONFIG_ROLES_PER_PAGE",
    "CONTEXT_MENU_NAME_LENGTH",
    "DB_COMMAND_NAME_LENGTH",
    "DB_DESCRIPTION_LENGTH",
    "DB_TARGET_TYPE_LENGTH",
    "DEFAULT_REASON",
    "DEPENDENCY_CACHE_SIZE",
    "EIGHT_BALL_QUESTION_LENGTH_LIMIT",
    "EIGHT_BALL_RESPONSE_WRAP_WIDTH",
    "EMBED_COLORS",
    "EMBED_FIELD_VALUE_LENGTH",
    "EMBED_ICONS",
    "EMBED_MAX_DESC_LENGTH",
    "EMBED_MAX_FIELDS",
    "EMBED_MAX_NAME_LENGTH",
    "EMBED_TOTAL_MAX",
    "EMOTES_PER_PAGE",
    "ENCODING_UTF8",
    "EXPLAINXKCD_BASE_URL",
    "FIELD_GUILD_ID",
    "FIELD_LEVEL",
    "FIELD_NAME",
    "FIELD_USER",
    "FILE_EXT_AVIF",
    "FILE_EXT_ENV",
    "FILE_EXT_GIF",
    "FILE_EXT_GIT",
    "FILE_EXT_JPEG",
    "FILE_EXT_JPG",
    "FILE_EXT_MD",
    "FILE_EXT_PNG",
    "FILE_EXT_PY",
    "FILE_EXT_WEBP",
    "GODBOLT_TIMEOUT",
    "HTTP_INTERNAL_ERROR",
    "HTTP_NOT_FOUND",
    "HTTP_OK",
    "HTTP_TIMEOUT",
    "MAX_DEPENDENCY_DEPTH",
    "MILLISECONDS_PER_SECOND",
    "NICKNAME_MAX_LENGTH",
    "RELOAD_TIMEOUT",
    "REMOVE_BOOKMARK",
    "ROLES_PER_PAGE",
    "SELECTS_MAX_OPTIONS",
    "SELECT_MAX_NAME_LENGTH",
    "SLASH_CMD_MAX_DESC_LENGTH",
    "SLASH_CMD_MAX_OPTIONS",
    "SLASH_CMD_NAME_LENGTH",
    "SLASH_OPTION_NAME_LENGTH",
    "SLOW_COG_LOAD_THRESHOLD",
    "SLOW_RESOLUTION_THRESHOLD",
    "SNIPPET_ALLOWED_CHARS_REGEX",
    "SNIPPET_MAX_NAME_LENGTH",
    "SNIPPET_PAGINATION_LIMIT",
    "TLDR_PAGES_URL",
    "TRUNCATION_SUFFIX",
    "WANDBOX_API_URL",
    "XKCD_BASE_URL",
]

# Color constants
EMBED_COLORS: Final[dict[str, int]] = {
    "DEFAULT": 16044058,
    "INFO": 12634869,
    "WARNING": 16634507,
    "ERROR": 16067173,
    "SUCCESS": 10407530,
    "POLL": 14724968,
    "CASE": 16217742,
    "NOTE": 16752228,
}

# Icon constants
EMBED_ICONS: Final[dict[str, str]] = {
    "DEFAULT": "https://i.imgur.com/owW4EZk.png",
    "INFO": "https://i.imgur.com/8GRtR2G.png",
    "SUCCESS": "https://i.imgur.com/JsNbN7D.png",
    "ERROR": "https://i.imgur.com/zZjuWaU.png",
    "CASE": "https://i.imgur.com/c43cwnV.png",
    "NOTE": "https://i.imgur.com/VqPFbil.png",
    "POLL": "https://i.imgur.com/pkPeG5q.png",
    "ACTIVE_CASE": "https://github.com/allthingslinux/tux/blob/main/assets/embeds/active_case.avif?raw=true",
    "INACTIVE_CASE": "https://github.com/allthingslinux/tux/blob/main/assets/embeds/inactive_case.avif?raw=true",
    "ADD": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/added.avif?raw=true",
    "REMOVE": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/removed.avif?raw=true",
    "BAN": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/ban.avif?raw=true",
    "JAIL": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/jail.avif?raw=true",
    "KICK": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/kick.avif?raw=true",
    "TIMEOUT": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/timeout.avif?raw=true",
    "WARN": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/warn.avif?raw=true",
}

# Embed limit constants
EMBED_MAX_NAME_LENGTH: Final[int] = 256
EMBED_MAX_DESC_LENGTH: Final[int] = 4096
EMBED_MAX_FIELDS: Final[int] = 25
EMBED_TOTAL_MAX: Final[int] = 6000
EMBED_FIELD_VALUE_LENGTH: Final[int] = 1024

NICKNAME_MAX_LENGTH: Final[int] = 32

# Interaction constants
ACTION_ROW_MAX_ITEMS: Final[int] = 5
SELECTS_MAX_OPTIONS: Final[int] = 25
SELECT_MAX_NAME_LENGTH: Final[int] = 100

# App commands constants
CONTEXT_MENU_NAME_LENGTH: Final[int] = 32
SLASH_CMD_NAME_LENGTH: Final[int] = 32
SLASH_CMD_MAX_DESC_LENGTH: Final[int] = 100
SLASH_CMD_MAX_OPTIONS: Final[int] = 25
SLASH_OPTION_NAME_LENGTH: Final[int] = 100

DEFAULT_REASON: Final[str] = "No reason provided"

# Snippet constants
SNIPPET_MAX_NAME_LENGTH: Final[int] = 20
SNIPPET_ALLOWED_CHARS_REGEX: Final[str] = r"^[a-zA-Z0-9-]+$"
SNIPPET_PAGINATION_LIMIT: Final[int] = 10

# Message timings
HTTP_TIMEOUT: Final[int] = 10

# General constants
TRUNCATION_SUFFIX: Final[str] = "..."

# AFK constants
AFK_PREFIX: Final[str] = "[AFK] "
AFK_SLEEPING_EMOJI: Final[str] = "\N{SLEEPING SYMBOL}"
AFK_ALLOWED_MENTIONS: Final[discord.AllowedMentions] = discord.AllowedMentions(
    users=False,
    everyone=False,
    roles=False,
)
AFK_REASON_MAX_LENGTH: Final[int] = 100

# 8ball constants
EIGHT_BALL_QUESTION_LENGTH_LIMIT: Final[int] = 120
EIGHT_BALL_RESPONSE_WRAP_WIDTH: Final[int] = 30

# Bookmark constants
ADD_BOOKMARK: Final[str] = "🔖"
REMOVE_BOOKMARK: Final[str] = "🗑️"

# Cog loading priorities
COG_PRIORITIES: Final[dict[str, int]] = {
    "services": 90,
    "config": 85,
    "admin": 80,
    "levels": 70,
    "moderation": 60,
    "snippets": 50,
    "guild": 40,
    "utility": 30,
    "info": 20,
    "fun": 10,
    "tools": 5,
    "plugins": 1,
}

# Performance thresholds
SLOW_RESOLUTION_THRESHOLD: Final[float] = 0.001  # 1ms in seconds
SLOW_COG_LOAD_THRESHOLD: Final[float] = 1.0  # seconds
MILLISECONDS_PER_SECOND: Final[int] = 1000

# Pagination limits
ROLES_PER_PAGE: Final[int] = 32
EMOTES_PER_PAGE: Final[int] = 128
BANS_LIMIT: Final[int] = 2000

# Config Dashboard pagination
CONFIG_RANKS_PER_PAGE: Final[int] = 5
CONFIG_ROLES_PER_PAGE: Final[int] = 5
CONFIG_COMMANDS_PER_PAGE: Final[int] = 5
CONFIG_LOGS_PER_PAGE: Final[int] = 5

# Config Dashboard colors (Discord brand colors)
CONFIG_COLOR_BLURPLE: Final[int] = 0x5865F2  # Discord blurple (primary)
CONFIG_COLOR_GREEN: Final[int] = 0x57F287  # Discord green (success)
CONFIG_COLOR_YELLOW: Final[int] = 0xFEE75C  # Discord yellow (warning)
CONFIG_COLOR_RED: Final[int] = 0xED4245  # Discord red (error/danger)

# Config Dashboard timeouts
CONFIG_DASHBOARD_TIMEOUT: Final[int] = 300  # 5 minutes

# Database field lengths
DB_DESCRIPTION_LENGTH: Final[int] = 500
DB_COMMAND_NAME_LENGTH: Final[int] = 200
DB_TARGET_TYPE_LENGTH: Final[int] = 20

# Service configuration
RELOAD_TIMEOUT: Final[float] = 30.0
MAX_DEPENDENCY_DEPTH: Final[int] = 10
DEPENDENCY_CACHE_SIZE: Final[int] = 1000
GODBOLT_TIMEOUT: Final[int] = 15

# HTTP status codes
HTTP_OK: Final[int] = 200
HTTP_NOT_FOUND: Final[int] = 404
HTTP_INTERNAL_ERROR: Final[int] = 500

# Common file extensions
FILE_EXT_PY: Final[str] = ".py"
FILE_EXT_PNG: Final[str] = ".png"
FILE_EXT_JPG: Final[str] = ".jpg"
FILE_EXT_JPEG: Final[str] = ".jpeg"
FILE_EXT_GIF: Final[str] = ".gif"
FILE_EXT_WEBP: Final[str] = ".webp"
FILE_EXT_AVIF: Final[str] = ".avif"
FILE_EXT_MD: Final[str] = ".md"
FILE_EXT_ENV: Final[str] = ".env"
FILE_EXT_GIT: Final[str] = ".git"

# Common encoding
ENCODING_UTF8: Final[str] = "utf-8"

# API URLs
XKCD_BASE_URL: Final[str] = "https://xkcd.com"
EXPLAINXKCD_BASE_URL: Final[str] = "https://www.explainxkcd.com/wiki/index.php/"
WANDBOX_API_URL: Final[str] = "https://wandbox.org/api/compile.json"
TLDR_PAGES_URL: Final[str] = (
    "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages"
)
ARCH_WIKI_API_URL: Final[str] = "https://wiki.archlinux.org/api.php"
ARCH_WIKI_BASE_URL: Final[str] = "https://wiki.archlinux.org/title/"

# Common field names
FIELD_GUILD_ID: Final[str] = "guild_id"
FIELD_USER: Final[str] = "user"
FIELD_NAME: Final[str] = "name"
FIELD_LEVEL: Final[str] = "level"
