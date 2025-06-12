"""Tests for the constants module."""

import pytest

from tux.utils.constants import CONST, Constants


class TestConstants:
    """Test cases for the Constants class."""

    @pytest.mark.parametrize("color_name", ["DEFAULT", "INFO", "WARNING", "ERROR", "SUCCESS", "POLL", "CASE", "NOTE"])
    def test_embed_colors_exist(self, color_name: str) -> None:
        """Test that all required embed colors are defined."""
        assert color_name in Constants.EMBED_COLORS
        assert isinstance(Constants.EMBED_COLORS[color_name], int)

    @pytest.mark.parametrize("icon_name", ["DEFAULT", "INFO", "SUCCESS", "ERROR", "CASE", "NOTE", "POLL"])
    def test_embed_icons_exist(self, icon_name: str) -> None:
        """Test that all required embed icons are defined."""
        assert icon_name in Constants.EMBED_ICONS
        assert isinstance(Constants.EMBED_ICONS[icon_name], str)
        assert Constants.EMBED_ICONS[icon_name].startswith("https://")

    def test_embed_limits(self):
        """Test that embed limit constants are correctly defined."""
        assert Constants.EMBED_MAX_NAME_LENGTH == 256
        assert Constants.EMBED_MAX_DESC_LENGTH == 4096
        assert Constants.EMBED_MAX_FIELDS == 25
        assert Constants.EMBED_TOTAL_MAX == 6000
        assert Constants.EMBED_FIELD_VALUE_LENGTH == 1024

    def test_default_reason(self):
        """Test that default reason is correctly defined."""
        assert Constants.DEFAULT_REASON == "No reason provided"

    def test_const_instance(self):
        """Test that CONST is an instance of Constants."""
        assert isinstance(CONST, Constants)

    def test_snippet_constants(self):
        """Test snippet-related constants."""
        assert Constants.SNIPPET_MAX_NAME_LENGTH == 20
        assert Constants.SNIPPET_ALLOWED_CHARS_REGEX == r"^[a-zA-Z0-9-]+$"
        assert Constants.SNIPPET_PAGINATION_LIMIT == 10

    def test_afk_constants(self):
        """Test AFK-related constants."""
        assert Constants.AFK_PREFIX == "[AFK] "
        assert Constants.AFK_TRUNCATION_SUFFIX == "..."

    def test_eight_ball_constants(self):
        """Test 8ball-related constants."""
        assert Constants.EIGHT_BALL_QUESTION_LENGTH_LIMIT == 120
        assert Constants.EIGHT_BALL_RESPONSE_WRAP_WIDTH == 30


@pytest.mark.parametrize(
    "color_name,expected_type",
    [
        ("DEFAULT", int),
        ("INFO", int),
        ("WARNING", int),
        ("ERROR", int),
        ("SUCCESS", int),
    ],
)
def test_embed_color_types(color_name: str, expected_type: type[int]) -> None:
    """Test that embed colors are of the correct type."""
    assert isinstance(Constants.EMBED_COLORS[color_name], expected_type)


@pytest.mark.parametrize("icon_name", ["DEFAULT", "INFO", "SUCCESS", "ERROR", "CASE", "NOTE", "POLL"])
def test_embed_icon_urls(icon_name: str) -> None:
    """Test that embed icon URLs are valid."""
    url = Constants.EMBED_ICONS[icon_name]
    assert url.startswith("https://")
    assert len(url) > 10  # Basic sanity check
