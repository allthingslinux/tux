"""Unified version detection and management system.

This module provides a clean, DRY approach to version handling across all environments:
- Development (git describe)
- Docker containers (VERSION file)
- Production releases (environment variables)
- Package metadata (fallback)

The system follows a clear priority order and provides consistent behavior.
"""

import os
import subprocess
import sys
from contextlib import suppress
from datetime import UTC, datetime
from pathlib import Path

try:
    import semver
except ImportError:
    semver = None


class VersionError(Exception):
    """Raised when version detection fails in an unexpected way."""


class VersionManager:
    """Centralized version detection and management.

    This class provides a single source of truth for version information
    across all environments and use cases.
    """

    def __init__(self, root_path: Path | None = None):
        """Initialize the version manager.

        Parameters
        ----------
        root_path : Path, optional
            Root path of the project. If None, will be auto-detected.
        """
        self.root_path = root_path or self._detect_root_path()
        self._version_cache: str | None = None

    def _detect_root_path(self) -> Path:
        """Detect the project root path.

        Returns
        -------
        Path
            The project root path.
        """
        # Start from the current file's directory and walk up
        current = Path(__file__).parent
        while current != current.parent:
            # Look for common project indicators
            if any(
                (current / indicator).exists()
                for indicator in ["pyproject.toml", "setup.py", "VERSION", ".git"]
            ):
                return current
            current = current.parent

        # Fallback to current working directory
        return Path.cwd()

    def get_version(self, force_refresh: bool = False) -> str:
        """Get the current version using the established priority order.

        Priority order:
        1. TUX_VERSION environment variable
        2. VERSION file in project root
        3. Git describe (if git is available)
        4. "dev" as final fallback

        Parameters
        ----------
        force_refresh : bool, default False
            If True, bypass cache and detect version fresh.

        Returns
        -------
        str
            The detected version string.
        """
        if not force_refresh and self._version_cache is not None:
            return self._version_cache

        version = self._detect_version()
        self._version_cache = version
        return version

    def _detect_version(self) -> str:
        """Detect version using the priority order.

        Returns
        -------
        str
            The detected version string.
        """
        if env_version := self._from_environment():
            return self._normalize_version(env_version)

        if file_version := self._from_version_file():
            return self._normalize_version(file_version)

        if git_version := self._from_git():
            return self._normalize_version(git_version)

        # Priority 4: Final fallback
        return "dev"

    def _from_environment(self) -> str | None:
        """Get version from TUX_VERSION environment variable.

        Returns
        -------
        str or None
            The version from environment, or None if not set.
        """
        return os.environ.get("TUX_VERSION", "").strip() or None

    def _from_version_file(self) -> str | None:
        """Get version from VERSION file in project root.

        Returns
        -------
        str or None
            The version from VERSION file, or None if not found.
        """
        version_file = self.root_path / "VERSION"
        if not version_file.exists():
            return None

        try:
            version = version_file.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeDecodeError):
            return None
        else:
            return version or None

    def _from_git(self) -> str | None:
        """Get version from git describe.

        Returns
        -------
        str or None
            The version from git describe, or None if git is unavailable.
        """
        # Check if we're in a git repository
        if not (self.root_path / ".git").exists():
            return None

        with suppress(subprocess.TimeoutExpired, FileNotFoundError, OSError):
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                capture_output=True,
                text=True,
                cwd=self.root_path,
                timeout=5,
                check=False,
            )

            if result.returncode != 0 or not result.stdout.strip():
                return None

            version = result.stdout.strip()
            # Remove 'v' prefix
            return version.removeprefix("v")

        return None

    def _normalize_version(self, version: str) -> str:
        """Normalize a version string using semver if available.

        Parameters
        ----------
        version : str
            The version string to normalize.

        Returns
        -------
        str
            The normalized version string.
        """
        if not version or not semver:
            return version

        try:
            # Parse and normalize using semver
            parsed = semver.Version.parse(version)
            return str(parsed)
        except (ValueError, TypeError):
            # If parsing fails, return the original version
            return version

    def is_semantic_version(self, version: str | None = None) -> bool:
        """Check if a version string is a valid semantic version.

        Parameters
        ----------
        version : str, optional
            The version to check. If None, uses the current detected version.

        Returns
        -------
        bool
            True if the version is valid semver, False otherwise.
        """
        if not semver:
            return False

        # Handle explicit empty string or None
        if version is not None and (not version or version.strip() == ""):
            return False

        # Use provided version or current detected version
        version_to_check = version if version is not None else self.get_version()

        try:
            semver.Version.parse(version_to_check)
        except (ValueError, TypeError):
            return False
        else:
            return True

    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two semantic version strings.

        Parameters
        ----------
        version1 : str
            First version to compare.
        version2 : str
            Second version to compare.

        Returns
        -------
        int
            -1 if version1 < version2, 0 if equal, 1 if version1 > version2.

        Raises
        ------
        ValueError
            If either version is not a valid semantic version.
        """
        if not semver:
            msg = "semver library is required for version comparison"
            raise ValueError(msg)

        try:
            v1 = semver.Version.parse(version1)
            v2 = semver.Version.parse(version2)
            return v1.compare(v2)
        except (ValueError, TypeError) as e:
            msg = f"Invalid version strings: {e}"
            raise ValueError(msg) from e

    def get_version_info(
        self,
        version: str | None = None,
    ) -> dict[str, str | int | None]:
        """Get detailed information about a semantic version.

        Parameters
        ----------
        version : str, optional
            The version to analyze. If None, uses the current detected version.

        Returns
        -------
        dict
            Dictionary containing version components and metadata.
        """
        version_to_check = version or self.get_version()

        if not semver or not self.is_semantic_version(version_to_check):
            return {
                "version": version_to_check,
                "major": None,
                "minor": None,
                "patch": None,
                "prerelease": None,
                "build": None,
                "is_valid": False,
            }

        try:
            parsed = semver.Version.parse(version_to_check)
            return {
                "version": str(parsed),
                "major": parsed.major,
                "minor": parsed.minor,
                "patch": parsed.patch,
                "prerelease": str(parsed.prerelease) if parsed.prerelease else None,
                "build": str(parsed.build) if parsed.build else None,
                "is_valid": True,
            }
        except (ValueError, TypeError):
            return {
                "version": version_to_check,
                "major": None,
                "minor": None,
                "patch": None,
                "prerelease": None,
                "build": None,
                "is_valid": False,
            }

    def get_build_info(self) -> dict[str, str]:
        """Get build information for the current version.

        Returns
        -------
        dict
            Dictionary containing build metadata.
        """
        version = self.get_version()
        git_sha = self._get_git_sha()

        return {
            "version": version,
            "git_sha": git_sha,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "is_semantic": str(self.is_semantic_version(version)),
        }

    def bump_version(self, version: str, bump_type: str) -> str:
        """Bump a semantic version.

        Parameters
        ----------
        version : str
            The version to bump.
        bump_type : str
            Type of bump: 'major', 'minor', 'patch'.

        Returns
        -------
        str
            The bumped version string.

        Raises
        ------
        ValueError
            If version is not semantic or bump_type is invalid.
        """
        if not semver:
            msg = "semver library required for version bumping"
            raise ValueError(msg)

        if not self.is_semantic_version(version):
            msg = f"Version '{version}' is not a valid semantic version"
            raise ValueError(msg)

        # Validate bump_type before parsing
        if bump_type not in ("major", "minor", "patch"):
            msg = f"Invalid bump_type '{bump_type}'. Use: major, minor, patch"
            raise ValueError(msg)

        try:
            parsed = semver.Version.parse(version)

            if bump_type == "major":
                new_version = parsed.bump_major()
            elif bump_type == "minor":
                new_version = parsed.bump_minor()
            elif bump_type == "patch":
                new_version = parsed.bump_patch()

            return str(new_version)
        except (ValueError, TypeError) as e:
            msg = f"Failed to bump version '{version}': {e}"
            raise ValueError(msg) from e

    def satisfies_constraint(self, version: str, constraint: str) -> bool:
        """Check if a version satisfies a semver constraint.

        Parameters
        ----------
        version : str
            Version to check.
        constraint : str
            Semver constraint (e.g., ">=1.0.0", "^1.2.0").

        Returns
        -------
        bool
            True if version satisfies the constraint.

        Raises
        ------
        ValueError
            If constraint syntax is invalid.
        """
        if not semver:
            msg = "semver library required for constraint checking"
            raise ValueError(msg)

        try:
            return semver.Version.parse(version).match(constraint)
        except (ValueError, TypeError) as e:
            msg = f"Invalid constraint '{constraint}': {e}"
            raise ValueError(msg) from e

    def generate_build_metadata(
        self,
        git_sha: str | None = None,
        build_date: str | None = None,
    ) -> str:
        """Generate build metadata string from git SHA and build date.

        Parameters
        ----------
        git_sha : str, optional
            Git SHA (short form). If None, attempts to detect from git.
        build_date : str, optional
            Build date in YYYYMMDD format. If None, uses current date.

        Returns
        -------
        str
            Build metadata string (e.g., "sha.abcdef.20231029").
        """
        if git_sha is None:
            git_sha = self._get_git_sha()

        if build_date is None:
            build_date = datetime.now(UTC).strftime("%Y%m%d")

        # Shorten SHA if needed
        if len(git_sha) > 7:
            git_sha = git_sha[:7]

        return f"sha.{git_sha}.{build_date}"

    def _get_git_sha(self) -> str:
        """Get the current git SHA.

        Returns
        -------
        str
            The git SHA, or "unknown" if not available.
        """
        if not (self.root_path / ".git").exists():
            return "unknown"

        with suppress(subprocess.TimeoutExpired, FileNotFoundError, OSError):
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.root_path,
                timeout=5,
                check=False,
            )

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()[:7]  # Short SHA

        return "unknown"


# Global instance for easy access
_version_manager = VersionManager()


# Convenience functions that use the global instance
def get_version() -> str:
    """Get the current version.

    Returns
    -------
    str
        The current version string.
    """
    return _version_manager.get_version()


def is_semantic_version(version: str | None = None) -> bool:
    """Check if a version is valid semantic version.

    Parameters
    ----------
    version : str, optional
        Version to check. If None, uses current version.

    Returns
    -------
    bool
        True if valid semver, False otherwise.
    """
    return _version_manager.is_semantic_version(version)


def compare_versions(version1: str, version2: str) -> int:
    """Compare two semantic versions.

    Parameters
    ----------
    version1 : str
        First version.
    version2 : str
        Second version.

    Returns
    -------
    int
        Comparison result (-1, 0, 1).
    """
    return _version_manager.compare_versions(version1, version2)


def get_version_info(version: str | None = None) -> dict[str, str | int | None]:
    """Get detailed version information.

    Parameters
    ----------
    version : str, optional
        Version to analyze. If None, uses current version.

    Returns
    -------
    dict
        Version information dictionary.
    """
    return _version_manager.get_version_info(version)


def get_build_info() -> dict[str, str]:
    """Get build information.

    Returns
    -------
    dict
        Build information dictionary.
    """
    return _version_manager.get_build_info()


def bump_version(version: str, bump_type: str) -> str:
    """Bump a semantic version.

    Parameters
    ----------
    version : str
        The version to bump.
    bump_type : str
        Type of bump: 'major', 'minor', 'patch'.

    Returns
    -------
    str
        The bumped version string.
    """
    return _version_manager.bump_version(version, bump_type)


def satisfies_constraint(version: str, constraint: str) -> bool:
    """Check if a version satisfies a semver constraint.

    Parameters
    ----------
    version : str
        Version to check.
    constraint : str
        Semver constraint (e.g., ">=1.0.0", "^1.2.0").

    Returns
    -------
    bool
        True if version satisfies the constraint.
    """
    return _version_manager.satisfies_constraint(version, constraint)


def generate_build_metadata(
    git_sha: str | None = None,
    build_date: str | None = None,
) -> str:
    """Generate build metadata string from git SHA and build date.

    Parameters
    ----------
    git_sha : str, optional
        Git SHA (short form). If None, attempts to detect from git.
    build_date : str, optional
        Build date in YYYYMMDD format. If None, uses current date.

    Returns
    -------
    str
        Build metadata string (e.g., "sha.abcdef.20231029").
    """
    return _version_manager.generate_build_metadata(git_sha, build_date)
