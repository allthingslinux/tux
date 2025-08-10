"""Type definitions for Tux core components."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import discord
from discord.ext import commands

if TYPE_CHECKING:
    from tux.core.types import Tux
else:
    Tux = commands.Bot  # type: ignore[valid-type]

# Type variable for generic context types
T = TypeVar("T", bound=commands.Context["Tux"] | discord.Interaction)

__all__ = ["T", "Tux"]
