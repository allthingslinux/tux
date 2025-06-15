import contextlib
import subprocess
from pathlib import Path


def _get_version() -> str:
    """Get version using a simple, reliable approach."""

    # 1. Check for VERSION file first (created during Docker build)
    version_file = Path(__file__).parent.parent / "VERSION"
    if version_file.exists():
        with contextlib.suppress(Exception):
            if content := version_file.read_text().strip():
                return content

    # 2. Try to get version from git (works in most cases)
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

    # 3. Try package metadata (standard installations)
    with contextlib.suppress(Exception):
        from importlib import metadata

        return metadata.version("tux")
    # 4. Final fallback
    return "dev"


# Get version once at import time
__version__: str = _get_version()
