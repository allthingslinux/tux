"""Utilities for generating discord.py FlagConverter classes at runtime.

This supports the dynamic moderation command system: given a command
configuration, generate a `commands.FlagConverter` subclass that exposes the
expected flags (duration, purge, silent, etc.).  This allows discord.py's
native flag parsing to work for both prefix and slash commands *and* lets the
custom help command auto-document the available flags.
"""
from __future__ import annotations

from typing import Any, Dict

import discord
from discord.ext import commands

__all__ = ["build_flag_converter"]


def _add_flag(attrs: Dict[str, Any], name: str, **kwargs: Any) -> None:
    """Helper to add a commands.flag entry to *attrs* if not already present."""
    if name not in attrs:
        attrs[name] = commands.flag(**kwargs)


def build_flag_converter(identifier: str, *, duration: bool, purge: bool, silent: bool) -> type[commands.FlagConverter] | None:  # noqa: D401
    """Return a `FlagConverter` subclass for the given flags.

    Parameters
    ----------
    identifier:
        A unique string (command name) used to build the class name.
    duration / purge / silent:
        Booleans indicating whether those flags are enabled.

    Returns
    -------
    type[commands.FlagConverter] | None
        The dynamically created converter class, or *None* if no flags were
        requested.
    """
    attrs: Dict[str, Any] = {}

    if duration:
        _add_flag(
            attrs,
            "duration",
            description="Duration (e.g. 14d)",
            aliases=["d"],
            default=None,
            positional=True,
        )

    if purge:
        _add_flag(
            attrs,
            "purge",
            description="Days of messages to delete (0-7)",
            aliases=["p"],
            default=0,
        )

    if silent:
        _add_flag(
            attrs,
            "silent",
            description="Don't DM the target",
            aliases=["s", "quiet"],
            default=False,
        )

    # No flags → no converter needed
    if not attrs:
        return None

    cls_name = f"{identifier.title()}Flags"
    FlagsCls = type(cls_name, (commands.FlagConverter,), attrs)

    # Expose in module globals so `typing.get_type_hints` can resolve it when
    # the help command introspects the callback signature.
    globals()[cls_name] = FlagsCls
    return FlagsCls