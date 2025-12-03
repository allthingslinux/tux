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
    # Base classes and mixins
    "BaseModel",
    "SoftDeleteMixin",
    "UUIDMixin",
    # Enums
    "CaseType",
    "PermissionType",
    # Core models
    "Guild",
    "GuildConfig",
    # User features
    "AFK",
    "Levels",
    "Reminder",
    "Snippet",
    # Moderation system
    "Case",
    # Permission system
    "PermissionRank",
    "PermissionAssignment",
    "PermissionCommand",
    # Starboard system
    "Starboard",
    "StarboardMessage",
]
