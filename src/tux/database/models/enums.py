from __future__ import annotations

from enum import Enum


class PermissionType(str, Enum):
    MEMBER = "member"
    CHANNEL = "channel"
    CATEGORY = "category"
    ROLE = "role"
    COMMAND = "command"
    MODULE = "module"


class OnboardingStage(str, Enum):
    NOT_STARTED = "not_started"
    DISCOVERED = "discovered"
    INITIALIZED = "initialized"
    CONFIGURED = "configured"
    COMPLETED = "completed"


class CaseType(str, Enum):
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
