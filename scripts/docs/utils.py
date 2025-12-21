"""Shared utilities for documentation scripts."""

from pathlib import Path

from scripts.ui import print_error


def has_zensical_config() -> bool:
    """Check if the project has a zensical.toml file."""
    if (Path.cwd() / "zensical.toml").exists():
        return True
    print_error("Can't find zensical.toml file. Please run from the project root.")
    return False


def has_wrangler_config() -> bool:
    """Check if the project has a wrangler.toml file."""
    if (Path.cwd() / "wrangler.toml").exists():
        return True
    print_error("wrangler.toml not found. Please run from the project root.")
    return False
