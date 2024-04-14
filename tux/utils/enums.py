from enum import Enum


class InfractionType(Enum):
    BAN = "ban"
    WARN = "warn"
    KICK = "kick"
    TIMEOUT = "timeout"
