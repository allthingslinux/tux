from pathlib import Path

from single_source import get_version

# Dynamically get the version from pyproject.toml
__version__ = get_version("tux", Path(__file__).parent.parent)
