"""
Tux Discord Bot Package Initialization.

This module handles version detection for the Tux Discord bot using a robust
fallback strategy that works across different deployment scenarios including
development, Docker containers, and PyPI installations.

Notes
-----
The version detection follows this priority order:
1. TUX_VERSION environment variable (runtime override)
2. VERSION file (Docker builds and deployments)
3. Git tags (development environments)
4. Package metadata (PyPI installations)
5. Fallback to "dev" if all methods fail

This approach ensures reliable version reporting regardless of how the bot
is deployed or executed.
"""

import os
import subprocess
from importlib import metadata
from pathlib import Path


def _get_version() -> str:
    """
    Retrieve the application version using multiple fallback strategies.

    This function attempts to determine the version using several methods in
    priority order, ensuring version detection works in all deployment scenarios.

    Returns
    -------
    str
        The detected version string, or "dev" if detection fails.

    Notes
    -----
    Fallback Strategy:
        1. Environment variable (TUX_VERSION) - Allows runtime version override
        2. VERSION file - Created during Docker builds for consistent versioning
        3. Git describe - Uses git tags for development environments
        4. Package metadata - Standard approach for PyPI installations
        5. "dev" fallback - Ensures a version is always returned

    This function is designed to never raise exceptions. All errors are
    silently handled to ensure the application can start even if version
    detection encounters issues.
    """
    root = Path(__file__).parent.parent

    def from_env() -> str:
        """
        Retrieve version from TUX_VERSION environment variable.

        This method provides the highest priority for version detection,
        allowing runtime override of the version string.

        Returns
        -------
        str
            Environment variable value, or empty string if not set.

        Notes
        -----
        Useful for:
        - Testing with specific version strings
        - Deployment environments with custom versioning
        - CI/CD pipelines that need to override detected versions
        """
        return os.environ.get("TUX_VERSION", "").strip()

    def from_file() -> str:
        """
        Retrieve version from VERSION file in the project root.

        This method reads a VERSION file that is typically created during
        Docker builds or deployment processes. It provides consistent
        versioning for containerized deployments where git history may
        not be available.

        Returns
        -------
        str
            Contents of VERSION file, or empty string if file doesn't exist.

        Notes
        -----
        The VERSION file is typically created during Docker builds and contains
        a single line with the version string. This method is preferred for
        containerized deployments where git history is not available.
        """
        version_file = root / "VERSION"
        return version_file.read_text().strip() if version_file.exists() else ""

    def from_git() -> str:
        """
        Retrieve version from git tags using git describe.

        This method uses git describe to generate version strings from git tags,
        making it ideal for development environments where the full git history
        is available.

        Returns
        -------
        str
            Git-generated version string with 'v' prefix removed,
            or empty string if git is unavailable or fails.

        Notes
        -----
        The version includes:
        - Exact tag name for released versions
        - Tag + commit count + SHA for development builds
        - "--dirty" suffix for uncommitted changes

        Only attempts git operations if .git directory exists to avoid
        unnecessary subprocess calls in non-git environments.
        """
        # Only attempt git operations if .git directory exists
        if not (root / ".git").exists():
            return ""

        # Execute git describe with comprehensive flags
        result = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            capture_output=True,
            text=True,
            cwd=root,
            timeout=5,  # Prevent hanging on network-mounted git repos
            check=False,  # Don't raise on non-zero exit codes
        )

        # Validate git command succeeded and produced output
        if result.returncode != 0 or not result.stdout.strip():
            return ""

        version = result.stdout.strip()
        # Remove common 'v' prefix from version tags (e.g., 'v1.0.0' -> '1.0.0')
        return version.removeprefix("v")

    def from_metadata() -> str:
        """
        Retrieve version from package metadata.

        This method uses Python's importlib.metadata to read the version
        from the installed package's metadata. This is the standard approach
        for packages installed via pip from PyPI or local wheels.

        Returns
        -------
        str
            Package version from metadata.

        Raises
        ------
        PackageNotFoundError
            If the package is not installed or metadata is unavailable.
        AttributeError
            If metadata module is not available (Python < 3.8).
        Various other exceptions
            If package metadata is corrupted or inaccessible.

        Notes
        -----
        All exceptions are handled by the caller to ensure robust version
        detection that never crashes the application startup process.
        """
        return metadata.version("tux")

    # Attempt each version detection method in priority order
    # Stop at the first method that returns a non-empty, non-placeholder version string
    for getter in (from_env, from_file, from_git, from_metadata):
        try:
            version = getter()
        except Exception as e:
            # Log the specific error to aid debugging while continuing to next method
            # This maintains robustness while providing visibility into version detection issues
            import logging  # noqa: PLC0415

            logging.getLogger(__name__).debug(f"Version detection method {getter.__name__} failed: {e}")
            continue
        # Check for valid version (non-empty and not placeholder values)
        if version and version not in ("0.0.0", "0.0", "unknown"):
            return version

    # Fallback version when all detection methods fail
    # Indicates development/unknown version rather than causing errors
    return "dev"


# Module-level version constant
# Computed once at import time for optimal performance and consistency
__version__: str = _get_version()
