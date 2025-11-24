"""
Utility functions for the help command system.

This module contains utility functions for formatting, categorizing,
and navigating help command content.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from discord.ext import commands


def format_multiline_description(text: str | None) -> str:
    """
    Format a multiline description with quote formatting for each line.

    Parameters
    ----------
    text : str | None
        The text to format.

    Returns
    -------
    str
        The formatted text with > prepended to each line.
    """
    if not text:
        text = "No documentation available."
    return "\n".join(f"> {line}" for line in text.split("\n"))


def truncate_description(text: str, max_length: int = 100) -> str:
    """
    Truncate a description to a maximum length.

    Parameters
    ----------
    text : str
        The text to truncate.
    max_length : int, optional
        Maximum length before truncation, by default 100.

    Returns
    -------
    str
        The truncated text with ellipsis if needed.
    """
    if not text:
        return "No description"

    return text if len(text) <= max_length else f"{text[: max_length - 3]}..."


def paginate_items(items: list[Any], page_size: int) -> list[list[Any]]:
    """
    Split items into pages of specified size.

    Parameters
    ----------
    items : list[Any]
        The items to paginate.
    page_size : int
        Maximum number of items per page.

    Returns
    -------
    list[list[Any]]
        A list of pages, each containing up to page_size items.
    """
    pages: list[list[Any]] = []

    pages.extend(items[i : i + page_size] for i in range(0, len(items), page_size))
    # Ensure at least one page even if no items
    if not pages and items:
        pages = [items]

    return pages


def create_cog_category_mapping(
    mapping: Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]],
) -> tuple[
    dict[str, dict[str, str]],
    dict[str, dict[str, commands.Command[Any, Any, Any]]],
]:
    """
    Create a mapping of command categories and commands.

    Parameters
    ----------
    mapping : Mapping[commands.Cog | None, list[commands.Command[Any, Any, Any]]]
        Mapping of cogs to their commands.

    Returns
    -------
    tuple[dict[str, dict[str, str]], dict[str, dict[str, commands.Command[Any, Any, Any]]]]
        A tuple of (category_cache, command_mapping).
    """
    command_categories: dict[str, dict[str, str]] = {}
    command_mapping: dict[str, dict[str, commands.Command[Any, Any, Any]]] = {}

    for cog, cog_commands in mapping.items():
        if cog and cog_commands:
            # Extract the group using the cog's module name
            cog_group = extract_cog_group(cog) or "extra"
            command_categories.setdefault(cog_group, {})
            command_mapping.setdefault(cog_group, {})

            for command in cog_commands:
                # Format command aliases for category display
                cmd_aliases = (
                    ", ".join(f"`{alias}`" for alias in command.aliases)
                    if command.aliases
                    else "`No aliases`"
                )
                command_categories[cog_group][command.name] = cmd_aliases
                command_mapping[cog_group][command.name] = command

    return command_categories, command_mapping


def extract_cog_group(cog: commands.Cog) -> str | None:
    """
    Extract the cog group from a cog's module path.

    Parameters
    ----------
    cog : commands.Cog
        The cog to extract the group from.

    Returns
    -------
    str | None
        The group name or None if no group found.
    """
    module = getattr(cog, "__module__", "")
    parts = module.split(".")

    # Assuming the structure is: tux.modules.<group>...
    if len(parts) >= 3 and parts[1].lower() == "modules":
        return parts[2].lower()
    return None


def get_cog_groups() -> list[str]:
    """Retrieve a list of module groups from the 'modules' folder.

    Returns
    -------
        A list of module group names.
    """
    modules_dir = Path(__file__).parent.parent / "modules"
    return [
        d.name
        for d in modules_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]


def is_large_command_group(command: commands.Group[Any, Any, Any]) -> bool:
    """
    Check if a command group is large and needs special handling.

    Parameters
    ----------
    command : commands.Group[Any, Any, Any]
        The command group to check.

    Returns
    -------
    bool
        True if the command group is large, False otherwise.
    """
    return command.name in {"jsk", "jishaku"} or len(command.commands) > 15
