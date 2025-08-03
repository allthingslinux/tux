import tomllib
from typing import Any, Final

from tux.utils.config import workspace_root


def _load_constants() -> dict[str, Any]:
    """Load constants from the TOML configuration file."""
    constants_path = workspace_root / "assets" / "data" / "constants.toml"
    with constants_path.open("rb") as f:
        return tomllib.load(f)


class Constants:
    def __init__(self) -> None:
        data = _load_constants()

        self.EMBED_COLORS: Final[dict[str, int]] = data["embed_colors"]

        self.EMBED_ICONS: Final[dict[str, str]] = data["embed_icons"]

        embed_limits: dict[str, Any] = data["embed_limits"]
        self.EMBED_MAX_NAME_LENGTH: Final[int] = int(embed_limits["max_name_length"])
        self.EMBED_MAX_DESC_LENGTH: Final[int] = int(embed_limits["max_desc_length"])
        self.EMBED_MAX_FIELDS: Final[int] = int(embed_limits["max_fields"])
        self.EMBED_TOTAL_MAX: Final[int] = int(embed_limits["total_max"])
        self.EMBED_FIELD_VALUE_LENGTH: Final[int] = int(embed_limits["field_value_length"])

        discord_limits: dict[str, Any] = data["discord_limits"]
        self.NICKNAME_MAX_LENGTH: Final[int] = int(discord_limits["nickname_max_length"])
        self.CONTEXT_MENU_NAME_LENGTH: Final[int] = int(discord_limits["context_menu_name_length"])
        self.SLASH_CMD_NAME_LENGTH: Final[int] = int(discord_limits["slash_cmd_name_length"])
        self.SLASH_CMD_MAX_DESC_LENGTH: Final[int] = int(discord_limits["slash_cmd_max_desc_length"])
        self.SLASH_CMD_MAX_OPTIONS: Final[int] = int(discord_limits["slash_cmd_max_options"])
        self.SLASH_OPTION_NAME_LENGTH: Final[int] = int(discord_limits["slash_option_name_length"])

        interaction_limits: dict[str, Any] = data["interaction_limits"]
        self.ACTION_ROW_MAX_ITEMS: Final[int] = int(interaction_limits["action_row_max_items"])
        self.SELECTS_MAX_OPTIONS: Final[int] = int(interaction_limits["selects_max_options"])
        self.SELECT_MAX_NAME_LENGTH: Final[int] = int(interaction_limits["select_max_name_length"])

        defaults: dict[str, Any] = data["defaults"]
        self.DEFAULT_REASON: Final[str] = str(defaults["reason"])
        self.DEFAULT_DELETE_AFTER: Final[int] = int(defaults["delete_after"])

        snippet_config: dict[str, Any] = data["snippet_config"]
        self.SNIPPET_MAX_NAME_LENGTH: Final[int] = int(snippet_config["max_name_length"])
        self.SNIPPET_ALLOWED_CHARS_REGEX: Final[str] = str(snippet_config["allowed_chars_regex"])
        self.SNIPPET_PAGINATION_LIMIT: Final[int] = int(snippet_config["pagination_limit"])

        afk_config: dict[str, Any] = data["afk_config"]
        self.AFK_PREFIX: Final[str] = str(afk_config["prefix"])
        self.AFK_TRUNCATION_SUFFIX: Final[str] = str(afk_config["truncation_suffix"])

        eight_ball_config: dict[str, Any] = data["eight_ball_config"]
        self.EIGHT_BALL_QUESTION_LENGTH_LIMIT: Final[int] = int(eight_ball_config["question_length_limit"])
        self.EIGHT_BALL_RESPONSE_WRAP_WIDTH: Final[int] = int(eight_ball_config["response_wrap_width"])

        bookmark_config: dict[str, Any] = data["bookmark_config"]
        self.ADD_BOOKMARK: Final[str] = str(bookmark_config["add_emoji"])
        self.REMOVE_BOOKMARK: Final[str] = str(bookmark_config["remove_emoji"])


CONST = Constants()
