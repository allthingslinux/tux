"""
🚀 Version Module Functions Tests - Convenience Function Testing.

Tests for module-level convenience functions in the version system.
"""

from tux.shared.version import (
    bump_version,
    compare_versions,
    generate_build_metadata,
    get_build_info,
    get_version,
    get_version_info,
    is_semantic_version,
    satisfies_constraint,
)


class TestModuleLevelFunctions:
    """Test the module-level convenience functions."""

    def test_get_version_function(self) -> None:
        """Test the get_version convenience function."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_is_semantic_version_function(self) -> None:
        """Test the is_semantic_version convenience function."""
        assert is_semantic_version("1.0.0") is True
        assert is_semantic_version("invalid") is False

    def test_compare_versions_function(self) -> None:
        """Test the compare_versions convenience function."""
        assert compare_versions("1.0.0", "2.0.0") == -1
        assert compare_versions("2.0.0", "1.0.0") == 1
        assert compare_versions("1.0.0", "1.0.0") == 0

    def test_get_version_info_function(self) -> None:
        """Test the get_version_info convenience function."""
        info = get_version_info("1.2.3")
        assert info["major"] == 1
        assert info["minor"] == 2
        assert info["patch"] == 3
        assert info["is_valid"] is True

    def test_get_build_info_function(self) -> None:
        """Test the get_build_info convenience function."""
        info = get_build_info()
        assert "version" in info
        assert "git_sha" in info
        assert "python_version" in info
        assert "is_semantic" in info

    def test_bump_version_function(self) -> None:
        """Test the bump_version convenience function."""
        assert bump_version("1.0.0", "patch") == "1.0.1"
        assert bump_version("1.0.0", "minor") == "1.1.0"
        assert bump_version("1.0.0", "major") == "2.0.0"
        # Note: prerelease bumping typically requires manual management of identifiers

    def test_satisfies_constraint_function(self) -> None:
        """Test the satisfies_constraint convenience function."""
        # Test basic comparison operators supported by semver.match
        assert satisfies_constraint("1.2.3", ">=1.0.0") is True
        assert satisfies_constraint("1.2.3", "<2.0.0") is True
        assert satisfies_constraint("2.0.0", ">=1.0.0") is True
        assert satisfies_constraint("0.9.0", ">=1.0.0") is False

    def test_generate_build_metadata_function(self) -> None:
        """Test the generate_build_metadata convenience function."""
        metadata = generate_build_metadata("abc123", "20231029")
        assert metadata == "sha.abc123.20231029"

        # Test with auto-detection (will use actual git SHA and current date)
        metadata = generate_build_metadata()
        assert "sha." in metadata
        assert len(metadata.split(".")) == 3
