"""
Database Models for Tux Bot.

This module contains all SQLModel-based database models used by the Tux Discord bot,
including base classes, mixins, enums, and specific model classes for various
features like moderation, levels, snippets, and guild configuration.
"""

from __future__ import annotations

# Import base classes and enums
from .base import BaseModel, SoftDeleteMixin, UUIDMixin
from .enums import CaseType, PermissionType
from .models import (
    AFK,
    Case,
    Guild,
    GuildConfig,
    Levels,
    PermissionAssignment,
    PermissionCommand,
    PermissionRank,
    Reminder,
    Snippet,
    Starboard,
    StarboardMessage,
)

__all__ = [
    "AFK",
    "BaseModel",
    "Case",
    "CaseType",
    "Guild",
    "GuildConfig",
    "Levels",
    "PermissionAssignment",
    "PermissionCommand",
    "PermissionRank",
    "PermissionType",
    "Reminder",
    "Snippet",
    "SoftDeleteMixin",
    "Starboard",
    "StarboardMessage",
    "UUIDMixin",
]
