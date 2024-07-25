import discord
from discord.ext import commands
from discord.utils import MISSING

from prisma.enums import CaseType


class BanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member ban.",
        aliases=["r"],
        default=MISSING,
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="Number of days in messages",
        aliases=["p", "purge"],
        default=0,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TempBanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member temp ban.",
        aliases=["r"],
        default=MISSING,
    )
    expires_at: int = commands.flag(
        name="expires_at",
        description="The time in days the ban will last for.",
        aliases=["t", "d", "e"],
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="The number of days (< 7) to purge in messages.",
        aliases=["p"],
        default=0,
    )


class KickFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member kick.",
        aliases=["r"],
        default="No reason provided.",
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TimeoutFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    duration: str = commands.flag(
        name="duration",
        description="The duration of the timeout.",
        aliases=["d"],
        default="1h",
    )
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member ban.",
        aliases=["r"],
        default=MISSING,
    )

    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnbanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    username_or_id: str = commands.flag(
        name="username_or_id",
        description="The username or ID of the user to ban.",
    )
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member ban.",
        aliases=["r"],
        default=MISSING,
    )


class JailFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member jail.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnjailFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member unjail.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class CasesViewFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    type: CaseType = commands.flag(
        name="case_type",
        description="The case type to view.",
        aliases=["t"],
        default=None,
    )
    target: discord.Member = commands.flag(
        name="case_target",
        description="The member to view cases for.",
        aliases=["memb", "m", "user", "u"],
        default=None,
    )
    moderator: discord.Member = commands.flag(
        name="case_moderator",
        description="The moderator to view cases for.",
        aliases=["mod"],
        default=None,
    )


class CaseModifyFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="case_reason",
        description="The modified reason.",
        aliases=["r"],
    )
    status: bool = commands.flag(
        name="case_status",
        description="The status of the case.",
        aliases=["s"],
    )
