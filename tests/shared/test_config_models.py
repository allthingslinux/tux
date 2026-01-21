"""
Tests for Pydantic config models in tux.shared.config.models.

Covers BotInfo.ACTIVITIES validator and other model behavior.
"""

from typing import Any

import pytest

from tux.shared.config.models import BotInfo

pytestmark = pytest.mark.unit


def _bot_info(*, activities: Any = None, **kwargs: Any) -> BotInfo:
    """Build BotInfo with ACTIVITIES and defaulted BOT_NAME, HIDE_BOT_OWNER, PREFIX."""
    return BotInfo(
        BOT_NAME="Tux",
        HIDE_BOT_OWNER=False,
        PREFIX="$",
        ACTIVITIES=activities,
        **kwargs,
    )


class TestBotInfoActivities:
    """Tests for BotInfo.ACTIVITIES field validator."""

    def test_activities_none_becomes_empty_list(self) -> None:
        """ACTIVITIES=None is normalized to []."""
        info = _bot_info(activities=None)
        assert info.ACTIVITIES == []

    def test_activities_empty_list(self) -> None:
        """ACTIVITIES=[] is preserved."""
        info = _bot_info(activities=[])
        assert info.ACTIVITIES == []

    def test_activities_list_preserved(self) -> None:
        """ACTIVITIES as list is preserved."""
        activities = [{"type": "playing", "name": "with Linux"}]
        info = _bot_info(activities=activities)
        assert activities == info.ACTIVITIES

    def test_activities_dict_wrapped_in_list(self) -> None:
        """ACTIVITIES as single dict is wrapped in a one-element list."""
        d = {"type": "streaming", "name": "x", "url": "https://a.b"}
        info = _bot_info(activities=d)
        assert [d] == info.ACTIVITIES

    def test_activities_json_string_list(self) -> None:
        """ACTIVITIES as JSON string of a list is parsed."""
        info = _bot_info(activities='[{"type":"playing","name":"y"}]')
        assert info.ACTIVITIES == [{"type": "playing", "name": "y"}]

    def test_activities_json_string_object_wrapped(self) -> None:
        """ACTIVITIES as JSON string of an object is parsed and wrapped in a list."""
        info = _bot_info(activities='{"type":"playing","name":"z"}')
        assert info.ACTIVITIES == [{"type": "playing", "name": "z"}]

    def test_activities_empty_string_becomes_empty_list(self) -> None:
        """ACTIVITIES as blank string is normalized to []."""
        info = _bot_info(activities="")
        assert info.ACTIVITIES == []

    def test_activities_whitespace_only_becomes_empty_list(self) -> None:
        """ACTIVITIES as whitespace-only string is normalized to []."""
        info = _bot_info(activities="   ")
        assert info.ACTIVITIES == []

    def test_activities_invalid_json_raises(self) -> None:
        """ACTIVITIES as invalid JSON string raises ValueError."""
        with pytest.raises(ValueError, match="valid JSON"):
            _bot_info(activities="{invalid}")

    def test_activities_json_number_raises(self) -> None:
        """ACTIVITIES as JSON that decodes to a number raises ValueError."""
        with pytest.raises(ValueError, match="list or object"):
            _bot_info(activities="42")

    def test_activities_json_string_raises(self) -> None:
        """ACTIVITIES as JSON that decodes to a string raises ValueError."""
        with pytest.raises(ValueError, match="list or object"):
            _bot_info(activities='"just a string"')
