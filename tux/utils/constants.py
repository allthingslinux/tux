from typing import Final


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
    EMBED_ICONS: Final[dict[str, str]] = {
        "DEFAULT": "https://i.imgur.com/owW4EZk.png",
        "INFO": "https://i.imgur.com/8GRtR2G.png",
        "SUCCESS": "https://i.imgur.com/JsNbN7D.png",
        "ERROR": "https://i.imgur.com/zZjuWaU.png",
        "CASE": "https://i.imgur.com/c43cwnV.png",
        "NOTE": "https://i.imgur.com/VqPFbil.png",
        "POLL": "https://i.imgur.com/pkPeG5q.png",
        "ACTIVE_CASE": "https://github.com/allthingslinux/tux/blob/main/assets/embeds/active_case.png?raw=true",
        "INACTIVE_CASE": "https://github.com/allthingslinux/tux/blob/main/assets/embeds/inactive_case.png?raw=true",
        "ADD": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/added.png?raw=true",
        "REMOVE": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/removed.png?raw=true",
        "BAN": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/ban.png?raw=true",
        "JAIL": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/jail.png?raw=true",
        "KICK": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/kick.png?raw=true",
        "TIMEOUT": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/timeout.png?raw=true",
        "WARN": "https://github.com/allthingslinux/tux/blob/main/assets/emojis/warn.png?raw=true",
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

    # AFK constants
    AFK_PREFIX = "[AFK] "
    AFK_TRUNCATION_SUFFIX = "..."

    # 8ball constants
    EIGHT_BALL_QUESTION_LENGTH_LIMIT = 120
    EIGHT_BALL_RESPONSE_WRAP_WIDTH = 30

    # Bookmark constants
    ADD_BOOKMARK = "🔖"
    REMOVE_BOOKMARK = "🗑️"


CONST = Constants()
