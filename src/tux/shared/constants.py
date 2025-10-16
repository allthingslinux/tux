from typing import Final

import discord

# TODO: move to assets/data/ potentially


class Constants:
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
    # TODO: make this work with branches and tags
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
    EMBED_MAX_NAME_LENGTH = 256
    EMBED_MAX_DESC_LENGTH = 4096
    EMBED_MAX_FIELDS = 25
    EMBED_TOTAL_MAX = 6000
    EMBED_FIELD_VALUE_LENGTH = 1024

    NICKNAME_MAX_LENGTH = 32

    # Interaction constants
    ACTION_ROW_MAX_ITEMS = 5
    SELECTS_MAX_OPTIONS = 25
    SELECT_MAX_NAME_LENGTH = 100

    # App commands constants
    CONTEXT_MENU_NAME_LENGTH = 32
    SLASH_CMD_NAME_LENGTH = 32
    SLASH_CMD_MAX_DESC_LENGTH = 100
    SLASH_CMD_MAX_OPTIONS = 25
    SLASH_OPTION_NAME_LENGTH = 100

    DEFAULT_REASON = "No reason provided"

    # Snippet constants
    SNIPPET_MAX_NAME_LENGTH = 20
    SNIPPET_ALLOWED_CHARS_REGEX = r"^[a-zA-Z0-9-]+$"
    SNIPPET_PAGINATION_LIMIT = 10

    # Message timings
    DEFAULT_DELETE_AFTER = 30
    HTTP_TIMEOUT = 10

    # General constants
    TRUNCATION_SUFFIX = "..."

    # AFK constants
    AFK_PREFIX = "[AFK] "
    AFK_SLEEPING_EMOJI = "\N{SLEEPING SYMBOL}"
    AFK_ALLOWED_MENTIONS = discord.AllowedMentions(users=False, everyone=False, roles=False)
    AFK_REASON_MAX_LENGTH = 100

    # 8ball constants
    EIGHT_BALL_QUESTION_LENGTH_LIMIT = 120
    EIGHT_BALL_RESPONSE_WRAP_WIDTH = 30

    # Bookmark constants
    ADD_BOOKMARK = "🔖"
    REMOVE_BOOKMARK = "🗑️"

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
    SLOW_RESOLUTION_THRESHOLD = 0.001  # 1ms in seconds
    MILLISECONDS_PER_SECOND = 1000

    # Pagination limits
    ROLES_PER_PAGE = 32
    EMOTES_PER_PAGE = 128
    BANS_LIMIT = 2000

    # Database field lengths
    DB_DESCRIPTION_LENGTH = 500
    DB_COMMAND_NAME_LENGTH = 200
    DB_TARGET_TYPE_LENGTH = 20

    # Service configuration
    RELOAD_TIMEOUT = 30.0
    MAX_DEPENDENCY_DEPTH = 10
    DEPENDENCY_CACHE_SIZE = 1000
    GODBOLT_TIMEOUT = 15

    # HTTP status codes
    HTTP_OK = 200
    HTTP_NOT_FOUND = 404
    HTTP_INTERNAL_ERROR = 500

    # Common file extensions
    FILE_EXT_PY = ".py"
    FILE_EXT_PNG = ".png"
    FILE_EXT_JPG = ".jpg"
    FILE_EXT_JPEG = ".jpeg"
    FILE_EXT_GIF = ".gif"
    FILE_EXT_WEBP = ".webp"
    FILE_EXT_AVIF = ".avif"
    FILE_EXT_MD = ".md"
    FILE_EXT_ENV = ".env"
    FILE_EXT_GIT = ".git"

    # Common encoding
    ENCODING_UTF8 = "utf-8"

    # API URLs
    XKCD_BASE_URL = "https://xkcd.com"
    EXPLAINXKCD_BASE_URL = "https://www.explainxkcd.com/wiki/index.php/"
    WANDBOX_API_URL = "https://wandbox.org/api/compile.json"
    TLDR_PAGES_URL = "https://raw.githubusercontent.com/tldr-pages/tldr/main/pages"
    ARCH_WIKI_API_URL = "https://wiki.archlinux.org/api.php"
    ARCH_WIKI_BASE_URL = "https://wiki.archlinux.org/title/"

    # Common field names
    FIELD_GUILD_ID = "guild_id"
    FIELD_USER = "user"
    FIELD_NAME = "name"
    FIELD_LEVEL = "level"


CONST = Constants()
