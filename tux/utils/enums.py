from enum import Enum


class InfractionType(Enum):
    BAN = "ban"
    UNBAN = "unban"
    WARN = "warn"
    KICK = "kick"
    TIMEOUT = "timeout"
