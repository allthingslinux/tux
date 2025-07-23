import tomllib
from pathlib import Path
from typing import Final

# Get the absolute path to the assets/data directory
_ASSETS_DATA_PATH = Path(__file__).parent.parent.parent / "assets" / "data"


# Load colors and icons from data files
def _load_colors() -> dict[str, int]:
    """Load embed colors from TOML file."""
    colors_file = _ASSETS_DATA_PATH / "embed_colors.toml"
    with colors_file.open("rb") as f:
        data = tomllib.load(f)
    return data["colors"]


def _load_icons() -> dict[str, str]:
    """Load embed icons from TOML file."""
    icons_file = _ASSETS_DATA_PATH / "embed_icons.toml"
    with icons_file.open("rb") as f:
        data = tomllib.load(f)
    return data["icons"]


class Constants:
    # Color constants
    EMBED_COLORS: Final[dict[str, int]] = _load_colors()

    # Icon constants
    EMBED_ICONS: Final[dict[str, str]] = _load_icons()

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
