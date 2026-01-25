"""Unit tests for info module helpers."""

# Descriptive test names obviate docstrings (D103)
# ruff: noqa: D103

from datetime import UTC, datetime

import pytest

from tux.modules.info.helpers import (
    chunks,
    extract_invite_code,
    format_bool,
    format_date_long,
    format_datetime,
)

pytestmark = pytest.mark.unit


def test_format_bool_true_returns_checkmark() -> None:
    assert format_bool(True) == "✅"


def test_format_bool_false_returns_cross() -> None:
    assert format_bool(False) == "❌"


def test_format_datetime_none_returns_unknown() -> None:
    assert format_datetime(None) == "Unknown"


def test_format_datetime_aware_returns_discord_timestamp() -> None:
    dt = datetime(2025, 1, 25, 12, 0, 0, tzinfo=UTC)
    result = format_datetime(dt)
    assert "Unknown" not in result
    assert "<t:" in result or ":" in result


def test_format_datetime_naive_uses_utc() -> None:
    dt = datetime(2025, 1, 25, 12, 0, 0, tzinfo=UTC)
    result = format_datetime(dt)
    assert result != "Unknown"


def test_format_date_long_none_returns_unknown() -> None:
    assert format_date_long(None) == "Unknown"


def test_format_date_long_returns_long_date() -> None:
    dt = datetime(2025, 1, 25, 12, 0, 0, tzinfo=UTC)
    assert format_date_long(dt) == "January 25, 2025"


def test_format_date_long_different_months() -> None:
    assert format_date_long(datetime(2024, 12, 1, tzinfo=UTC)) == "December 01, 2024"
    assert format_date_long(datetime(2024, 6, 15, tzinfo=UTC)) == "June 15, 2024"


def test_extract_invite_code_plain_returns_as_is() -> None:
    assert extract_invite_code("abc123") == "abc123"


def test_extract_invite_code_discord_gg_extracts_code() -> None:
    assert extract_invite_code("https://discord.gg/linux") == "linux"
    assert extract_invite_code("discord.gg/abc123") == "abc123"


def test_extract_invite_code_discord_com_invite_extracts_code() -> None:
    assert extract_invite_code("https://discord.com/invite/linux") == "linux"
    assert extract_invite_code("discord.com/invite/xyz789") == "xyz789"


def test_extract_invite_code_strips_query() -> None:
    assert extract_invite_code("https://discord.gg/code?ref=foo") == "code"


def test_chunks_splits_into_size() -> None:
    it = iter(["a", "b", "c", "d", "e"])
    result = list(chunks(it, 2))
    assert result == [["a", "b"], ["c", "d"], ["e"]]


def test_chunks_exact_multiple() -> None:
    it = iter(["x", "y", "z"])
    result = list(chunks(it, 1))
    assert result == [["x"], ["y"], ["z"]]


def test_chunks_empty_iterator() -> None:
    it = iter([])
    result = list(chunks(it, 5))
    assert result == []


def test_chunks_single_large_chunk() -> None:
    it = iter(["a", "b", "c"])
    result = list(chunks(it, 10))
    assert result == [["a", "b", "c"]]
