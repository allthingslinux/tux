"""Type definitions for Tux core components."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import discord
from discord.ext import commands

if TYPE_CHECKING:
    # During static type checking, use the real Tux class from bot.py
    from tux.core.bot import Tux
else:
    # At runtime, we just need a reasonable alias to avoid import cycles
    Tux = commands.Bot  # type: ignore[valid-type]

# Type variable for generic context types
T = TypeVar("T", bound=commands.Context["Tux"] | discord.Interaction)

__all__ = ["T", "Tux"]
