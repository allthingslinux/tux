"""Tests for the constants module."""

from tux.utils.constants import CONST, Constants


class TestConstants:
    """Test cases for the Constants class."""

    def test_embed_limits(self):
        """Test that embed limit constants are correctly defined."""
        assert CONST.EMBED_MAX_NAME_LENGTH == 256
        assert CONST.EMBED_MAX_DESC_LENGTH == 4096
        assert CONST.EMBED_MAX_FIELDS == 25
        assert CONST.EMBED_TOTAL_MAX == 6000
        assert CONST.EMBED_FIELD_VALUE_LENGTH == 1024

    def test_discord_limits(self):
        """Test Discord-related limit constants."""
        assert CONST.NICKNAME_MAX_LENGTH == 32
        assert CONST.CONTEXT_MENU_NAME_LENGTH == 32
        assert CONST.SLASH_CMD_NAME_LENGTH == 32
        assert CONST.SLASH_CMD_MAX_DESC_LENGTH == 100
        assert CONST.SLASH_CMD_MAX_OPTIONS == 25
        assert CONST.SLASH_OPTION_NAME_LENGTH == 100

    def test_interaction_limits(self):
        """Test interaction-related constants."""
        assert CONST.ACTION_ROW_MAX_ITEMS == 5
        assert CONST.SELECTS_MAX_OPTIONS == 25
        assert CONST.SELECT_MAX_NAME_LENGTH == 100

    def test_default_values(self):
        """Test default value constants."""
        assert CONST.DEFAULT_REASON == "No reason provided"
        assert CONST.DEFAULT_DELETE_AFTER == 30

    def test_const_instance(self):
        """Test that CONST is an instance of Constants."""
        assert isinstance(CONST, Constants)

    def test_snippet_constants(self):
        """Test snippet-related constants."""
        assert CONST.SNIPPET_MAX_NAME_LENGTH == 20
        assert CONST.SNIPPET_ALLOWED_CHARS_REGEX == "^[a-zA-Z0-9-]+$"
        assert CONST.SNIPPET_PAGINATION_LIMIT == 10

    def test_afk_constants(self):
        """Test AFK-related constants."""
        assert CONST.AFK_PREFIX == "[AFK] "
        assert CONST.AFK_TRUNCATION_SUFFIX == "..."

    def test_eight_ball_constants(self):
        """Test 8ball-related constants."""
        assert CONST.EIGHT_BALL_QUESTION_LENGTH_LIMIT == 120
        assert CONST.EIGHT_BALL_RESPONSE_WRAP_WIDTH == 30

    def test_bookmark_constants(self):
        """Test bookmark-related constants."""
        assert CONST.ADD_BOOKMARK == "🔖"
        assert CONST.REMOVE_BOOKMARK == "🗑️"

    def test_embed_colors_loaded(self):
        """Test that embed colors are correctly loaded from TOML."""
        assert isinstance(CONST.EMBED_COLORS, dict)
        assert "DEFAULT" in CONST.EMBED_COLORS
        assert "INFO" in CONST.EMBED_COLORS
        assert "ERROR" in CONST.EMBED_COLORS
        assert isinstance(CONST.EMBED_COLORS["DEFAULT"], int)

    def test_embed_icons_loaded(self):
        """Test that embed icons are correctly loaded from TOML."""
        assert isinstance(CONST.EMBED_ICONS, dict)
        assert "DEFAULT" in CONST.EMBED_ICONS
        assert "INFO" in CONST.EMBED_ICONS
        assert "ERROR" in CONST.EMBED_ICONS
        assert isinstance(CONST.EMBED_ICONS["DEFAULT"], str)
        assert CONST.EMBED_ICONS["DEFAULT"].startswith("https://")

    def test_constants_file_loading(self):
        """Test that creating a new Constants instance loads data correctly."""
        new_const = Constants()
        assert new_const.DEFAULT_REASON == CONST.DEFAULT_REASON
        assert new_const.EMBED_COLORS == CONST.EMBED_COLORS
