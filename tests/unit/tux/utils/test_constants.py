"""Tests for the constants module."""

from tux.utils.constants import CONST, Constants


class TestConstants:
    """Test cases for the Constants class."""

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
