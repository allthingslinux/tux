"""Type definitions for Tux core components."""

from __future__ import annotations

from typing import TypeVar

import discord
from discord.ext import commands

# Type variable for generic context types
T = TypeVar("T", bound=commands.Context[commands.Bot] | discord.Interaction)

__all__ = ["T"]
