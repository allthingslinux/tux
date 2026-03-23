"""
Database model enums for Tux bot.

This module defines enumeration types used throughout the database models,
providing type-safe constants for permissions, onboarding stages, and case types.
"""

from __future__ import annotations

from enum import StrEnum


class PermissionType(StrEnum):
    """Types of permissions that can be configured in the system."""

    MEMBER = "member"
    CHANNEL = "channel"
    CATEGORY = "category"
    ROLE = "role"
    COMMAND = "command"
    MODULE = "module"


class OnboardingStage(StrEnum):
    """Stages of the guild onboarding process."""

    NOT_STARTED = "not_started"
    DISCOVERED = "discovered"
    INITIALIZED = "initialized"
    CONFIGURED = "configured"
    COMPLETED = "completed"


class CaseType(StrEnum):
    """Types of moderation cases that can be recorded in the system."""

    BAN = "BAN"
    UNBAN = "UNBAN"
    HACKBAN = "HACKBAN"
    TEMPBAN = "TEMPBAN"
    KICK = "KICK"
    TIMEOUT = "TIMEOUT"
    UNTIMEOUT = "UNTIMEOUT"
    WARN = "WARN"
    JAIL = "JAIL"
    UNJAIL = "UNJAIL"
    SNIPPETBAN = "SNIPPETBAN"
    SNIPPETUNBAN = "SNIPPETUNBAN"
    POLLBAN = "POLLBAN"
    POLLUNBAN = "POLLUNBAN"
