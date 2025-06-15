import contextlib
import os
import subprocess
from pathlib import Path


def _get_version() -> str:
    """Get version using a simple, reliable approach with environment variable support."""

    # 1. Check for TUX_VERSION environment variable first (highest priority)
    # This allows runtime override for deployments and testing
    if env_version := os.environ.get("TUX_VERSION", "").strip():
        return env_version

    # 2. Check for VERSION file (created during Docker build)
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        with contextlib.suppress(Exception):
            if content := version_file.read_text().strip():
                return content

    # 3. Try to get version from git (works in most cases but slower)
    # Only attempt if we're likely in a development environment
    if Path(__file__).parent.parent.joinpath(".git").exists():
        with contextlib.suppress(Exception):
            result = subprocess.run(
                ["git", "describe", "--tags", "--always", "--dirty"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
                timeout=5,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                version = result.stdout.strip()
                # Clean up git describe output to be more readable
                return version.removeprefix("v")  # Remove 'v' prefix

    # 4. Try package metadata (standard installations)
    with contextlib.suppress(Exception):
        from importlib import metadata

        return metadata.version("tux")

    # 5. Final fallback
    return "dev"


# Get version once at import time for performance
# PERFORMANCE: Avoids repeated git calls or file reads
__version__: str = _get_version()
