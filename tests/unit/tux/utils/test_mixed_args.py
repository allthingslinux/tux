from tux.utils.mixed_args import (
    extract_duration_from_args,
    extract_reason_from_args,
    generate_mixed_usage,
    is_duration,
    parse_mixed_arguments,
)


class TestIsDuration:
    """Test the is_duration function."""

    def test_valid_durations(self) -> None:
        """Test that valid duration strings return True."""
        valid_durations = [
            "30s",
            "5m",
            "2h",
            "14d",
            "1h30m",
            "2d5h",
            "1.5h",
            "0.5d",
        ]

        for duration in valid_durations:
            assert is_duration(duration), f"'{duration}' should be recognized as a duration"

    def test_invalid_durations(self) -> None:
        """Test that invalid duration strings return False."""
        invalid_durations = [
            "reason",
            "30",
            "5minutes",
            "2hours",
            "14days",
            "1h30",
            "invalid",
            "",
            "30x",
        ]

        for duration in invalid_durations:
            assert not is_duration(duration), f"'{duration}' should not be recognized as a duration"


class TestParseMixedArguments:
    """Test the parse_mixed_arguments function."""

    def test_positional_duration(self) -> None:
        """Test parsing duration as positional argument."""
        result = parse_mixed_arguments("14d reason")
        assert result["duration"] == "14d"
        assert result["reason"] == "reason"

    def test_flag_duration(self) -> None:
        """Test parsing duration as flag argument."""
        result = parse_mixed_arguments("reason -d 14d")
        assert result["duration"] == "14d"
        assert result["reason"] == "reason"

    def test_mixed_usage(self) -> None:
        """Test parsing mixed positional and flag arguments."""
        result = parse_mixed_arguments("14d reason -s")
        assert result["duration"] == "14d"
        assert result["reason"] == "reason"
        assert result["silent"] is True

    def test_positional_boolean(self) -> None:
        """Test parsing boolean as positional argument."""
        result = parse_mixed_arguments("true")
        assert result["silent"] is True

    def test_flag_boolean(self) -> None:
        """Test parsing boolean as flag argument."""
        result = parse_mixed_arguments("-s")
        assert result["silent"] is True

    def test_positional_number(self) -> None:
        """Test parsing number as positional argument."""
        result = parse_mixed_arguments("7")
        assert result["purge"] == 7

    def test_flag_number(self) -> None:
        """Test parsing number as flag argument."""
        result = parse_mixed_arguments("-p 7")
        assert result["purge"] == 7

    def test_multiple_flags(self) -> None:
        """Test parsing multiple flags."""
        result = parse_mixed_arguments("reason -d 14d -s -p 7")
        assert result["duration"] == "14d"
        assert result["reason"] == "reason"
        assert result["silent"] is True
        assert result["purge"] == 7

    def test_positional_takes_precedence(self) -> None:
        """Test that positional arguments take precedence over flags."""
        result = parse_mixed_arguments("14d reason -d 30d")
        assert result["duration"] == "14d"  # Positional takes precedence
        assert result["reason"] == "reason"

    def test_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_mixed_arguments("")
        assert result == {}

    def test_whitespace_only(self) -> None:
        """Test parsing whitespace-only string."""
        result = parse_mixed_arguments("   ")
        assert result == {}


class TestGenerateMixedUsage:
    """Test the generate_mixed_usage function."""

    def test_basic_usage(self) -> None:
        """Test generating basic usage string."""
        usage = generate_mixed_usage("timeout", ["member"], ["duration", "reason"], ["-d", "-s"])
        assert usage == "timeout <member> [duration|reason] [-d] [-s]"

    def test_no_optional_params(self) -> None:
        """Test generating usage with no optional parameters."""
        usage = generate_mixed_usage("ban", ["member"], [], ["-r", "-s"])
        assert usage == "ban <member> [-r] [-s]"

    def test_no_flags(self) -> None:
        """Test generating usage with no flags."""
        usage = generate_mixed_usage("kick", ["member"], ["reason"], [])
        assert usage == "kick <member> [reason]"

    def test_multiple_required_params(self) -> None:
        """Test generating usage with multiple required parameters."""
        usage = generate_mixed_usage("move", ["member", "channel"], ["reason"], ["-s"])
        assert usage == "move <member> <channel> [reason] [-s]"


class TestExtractFunctions:
    """Test the extract functions."""

    def test_extract_duration_from_args(self) -> None:
        """Test extracting duration from arguments."""
        args = ["reason", "14d", "other"]
        duration = extract_duration_from_args(args)
        assert duration == "14d"

    def test_extract_duration_not_found(self) -> None:
        """Test extracting duration when not present."""
        args = ["reason", "other"]
        duration = extract_duration_from_args(args)
        assert duration is None

    def test_extract_reason_from_args(self) -> None:
        """Test extracting reason from arguments."""
        args = ["reason", "14d", "other"]
        reason = extract_reason_from_args(args)
        assert reason == "reason"

    def test_extract_reason_not_found(self) -> None:
        """Test extracting reason when not present."""
        args = ["14d", "other"]
        reason = extract_reason_from_args(args)
        assert reason is None

    def test_extract_reason_with_flags(self) -> None:
        """Test extracting reason with flags present."""
        args = ["reason", "-d", "14d", "-s"]
        reason = extract_reason_from_args(args)
        assert reason == "reason"
