"""
🚀 Version Manager Tests - Version Detection and Management.

Tests for the VersionManager class and version detection logic.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from tux.shared.version import VersionManager


class TestVersionManager:
    """Test the VersionManager class."""

    def test_version_manager_initialization(self) -> None:
        """Test that VersionManager initializes correctly."""
        manager = VersionManager()
        assert manager.root_path is not None
        assert isinstance(manager.root_path, Path)

    def test_version_manager_with_custom_root(self) -> None:
        """Test VersionManager with custom root path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_root = Path(temp_dir)
            manager = VersionManager(custom_root)
            assert manager.root_path == custom_root

    def test_get_version_caching(self) -> None:
        """Test that version is cached after first call."""
        manager = VersionManager()

        # First call should detect version
        version1 = manager.get_version()

        # Second call should use cache
        version2 = manager.get_version()

        assert version1 == version2
        assert manager._version_cache == version1

    def test_get_version_force_refresh(self) -> None:
        """Test that force_refresh bypasses cache."""
        manager = VersionManager()

        # Get initial version
        version1 = manager.get_version()

        # Force refresh should detect again
        version2 = manager.get_version(force_refresh=True)

        # Should be the same (unless environment changed)
        assert version1 == version2

    def test_from_environment(self) -> None:
        """Test version detection from environment variable."""
        manager = VersionManager()

        with patch.dict(os.environ, {"TUX_VERSION": "1.2.3-env"}):
            version = manager._from_environment()
            assert version == "1.2.3-env"

    def test_from_environment_empty(self) -> None:
        """Test environment variable with empty value."""
        manager = VersionManager()

        with patch.dict(os.environ, {"TUX_VERSION": ""}):
            version = manager._from_environment()
            assert version is None

    def test_from_environment_whitespace(self) -> None:
        """Test environment variable with whitespace."""
        manager = VersionManager()

        with patch.dict(os.environ, {"TUX_VERSION": "  1.2.3  "}):
            version = manager._from_environment()
            assert version == "1.2.3"

    def test_from_version_file(self) -> None:
        """Test version detection from VERSION file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            version_file = root / "VERSION"
            version_file.write_text("2.0.0-file")

            manager = VersionManager(root)
            version = manager._from_version_file()
            assert version == "2.0.0-file"

    def test_from_version_file_not_exists(self) -> None:
        """Test version detection when VERSION file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = VersionManager(root)
            version = manager._from_version_file()
            assert version is None

    def test_from_version_file_empty(self) -> None:
        """Test version detection from empty VERSION file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            version_file = root / "VERSION"
            version_file.write_text("")

            manager = VersionManager(root)
            version = manager._from_version_file()
            assert version is None

    def test_from_version_file_whitespace(self) -> None:
        """Test version detection from VERSION file with whitespace."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            version_file = root / "VERSION"
            version_file.write_text("  3.0.0  \n")

            manager = VersionManager(root)
            version = manager._from_version_file()
            assert version == "3.0.0"

    def test_from_git_success(self) -> None:
        """Test successful git version detection."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            # Create a mock .git directory
            (root / ".git").mkdir()

            manager = VersionManager(root)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v4.0.0-10-gabc1234"

                version = manager._from_git()
                assert version == "4.0.0-10-gabc1234"

    def test_from_git_no_git_dir(self) -> None:
        """Test git version detection when .git doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = VersionManager(root)
            version = manager._from_git()
            assert version is None

    def test_from_git_command_failure(self) -> None:
        """Test git version detection when command fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()

            manager = VersionManager(root)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1
                mock_run.return_value.stdout = ""

                version = manager._from_git()
                assert version is None

    def test_from_git_timeout(self) -> None:
        """Test git version detection with timeout."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()

            manager = VersionManager(root)

            with patch("subprocess.run") as mock_run:
                mock_run.side_effect = TimeoutError("Command timed out")

                version = manager._from_git()
                assert version is None

    def test_normalize_version_with_semver(self) -> None:
        """Test version normalization with semver available."""
        manager = VersionManager()

        with patch("tux.shared.version.semver") as mock_semver:
            mock_version = Mock()
            mock_version.__str__ = Mock(return_value="1.0.0")
            mock_semver.Version.parse.return_value = mock_version

            result = manager._normalize_version("1.0.0")
            assert result == "1.0.0"

    def test_normalize_version_without_semver(self) -> None:
        """Test version normalization without semver."""
        manager = VersionManager()

        with patch("tux.shared.version.semver", None):
            result = manager._normalize_version("1.0.0")
            assert result == "1.0.0"

    def test_normalize_version_invalid(self) -> None:
        """Test version normalization with invalid version."""
        manager = VersionManager()

        with patch("tux.shared.version.semver") as mock_semver:
            mock_semver.Version.parse.side_effect = ValueError("Invalid version")

            result = manager._normalize_version("invalid-version")
            assert result == "invalid-version"

    def test_detect_version_priority_order(self) -> None:
        """Test that version detection follows correct priority order."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            # Create VERSION file
            version_file = root / "VERSION"
            version_file.write_text("2.0.0-file")

            # Create .git directory
            (root / ".git").mkdir()

            manager = VersionManager(root)

            # Test priority: env > file > git > dev
            with (
                patch.dict(os.environ, {"TUX_VERSION": "1.0.0-env"}),
                patch("subprocess.run") as mock_run,
            ):
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v3.0.0"

                version = manager._detect_version()
                assert version == "1.0.0-env"  # Environment should win

    def test_detect_version_file_priority(self) -> None:
        """Test that VERSION file has priority over git."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            # Create VERSION file
            version_file = root / "VERSION"
            version_file.write_text("2.0.0-file")

            # Create .git directory
            (root / ".git").mkdir()

            manager = VersionManager(root)

            # No environment variable
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("subprocess.run") as mock_run,
            ):
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v3.0.0"

                version = manager._detect_version()
                assert version == "2.0.0-file"  # File should win over git

    def test_detect_version_git_priority(self) -> None:
        """Test that git has priority over dev fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            # Create .git directory
            (root / ".git").mkdir()

            manager = VersionManager(root)

            # No environment variable or VERSION file
            with (
                patch.dict(os.environ, {}, clear=True),
                patch("subprocess.run") as mock_run,
            ):
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "v3.0.0"

                version = manager._detect_version()
                assert version == "3.0.0"  # Git should win over dev

    def test_detect_version_dev_fallback(self) -> None:
        """Test that dev is used as final fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = VersionManager(root)

            # No environment variable, VERSION file, or git
            with patch.dict(os.environ, {}, clear=True):
                version = manager._detect_version()
                assert version == "dev"  # Should fallback to dev

    def test_is_semantic_version_valid(self) -> None:
        """Test semantic version validation with valid versions."""
        manager = VersionManager()

        valid_versions = ["1.0.0", "1.0.0-rc.1", "1.0.0+build.1", "1.0.0-rc.1+build.1"]

        for version in valid_versions:
            assert manager.is_semantic_version(version), (
                f"Version {version} should be valid"
            )

    def test_is_semantic_version_invalid(self) -> None:
        """Test semantic version validation with invalid versions."""
        manager = VersionManager()

        invalid_versions = ["not-a-version", "1.0", "v1.0.0"]

        for version in invalid_versions:
            assert not manager.is_semantic_version(version), (
                f"Version {version} should be invalid"
            )

    def test_is_semantic_version_empty_string(self) -> None:
        """Test semantic version validation with empty string."""
        manager = VersionManager()
        assert not manager.is_semantic_version("")

    def test_is_semantic_version_none(self) -> None:
        """Test semantic version validation with None (uses current version)."""
        manager = VersionManager()
        # When None is passed, it uses the current detected version
        # which should be a valid semver in our test environment
        result = manager.is_semantic_version(None)
        assert isinstance(result, bool)  # Should return a boolean

    def test_compare_versions(self) -> None:
        """Test version comparison."""
        manager = VersionManager()

        assert manager.compare_versions("1.0.0", "2.0.0") == -1
        assert manager.compare_versions("2.0.0", "1.0.0") == 1
        assert manager.compare_versions("1.0.0", "1.0.0") == 0

    def test_compare_versions_invalid(self) -> None:
        """Test version comparison with invalid versions."""
        manager = VersionManager()

        with pytest.raises(ValueError, match=r".*"):
            manager.compare_versions("invalid", "1.0.0")

    def test_get_version_info(self) -> None:
        """Test getting detailed version information."""
        manager = VersionManager()

        info = manager.get_version_info("1.2.3-rc.1+build.1")
        assert info["major"] == 1
        assert info["minor"] == 2
        assert info["patch"] == 3
        assert info["prerelease"] == "rc.1"
        assert info["build"] == "build.1"
        assert info["is_valid"] is True

    def test_get_version_info_invalid(self) -> None:
        """Test getting version info for invalid version."""
        manager = VersionManager()

        info = manager.get_version_info("invalid-version")
        assert info["major"] is None
        assert info["minor"] is None
        assert info["patch"] is None
        assert info["prerelease"] is None
        assert info["build"] is None
        assert info["is_valid"] is False

    def test_get_build_info(self) -> None:
        """Test getting build information."""
        manager = VersionManager()

        info = manager.get_build_info()
        assert "version" in info
        assert "git_sha" in info
        assert "python_version" in info
        assert "is_semantic" in info

    def test_get_git_sha_success(self) -> None:
        """Test getting git SHA successfully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()

            manager = VersionManager(root)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 0
                mock_run.return_value.stdout = "abc1234567890def"

                sha = manager._get_git_sha()
                assert sha == "abc1234"  # Should be truncated to 7 chars

    def test_get_git_sha_no_git(self) -> None:
        """Test getting git SHA when no git directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = VersionManager(root)

            sha = manager._get_git_sha()
            assert sha == "unknown"

    def test_get_git_sha_failure(self) -> None:
        """Test getting git SHA when command fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".git").mkdir()

            manager = VersionManager(root)

            with patch("subprocess.run") as mock_run:
                mock_run.return_value.returncode = 1

                sha = manager._get_git_sha()
                assert sha == "unknown"
