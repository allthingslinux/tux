import discord
from discord.ext import commands
from discord.utils import MISSING

from prisma.enums import CaseType
from tux.utils.converters import CaseTypeConverter


class BanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the ban.",
        aliases=["r"],
        default=MISSING,
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="The number of days (< 7) to purge in messages.",
        aliases=["p", "purge"],
        default=0,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TempBanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the temp ban.",
        aliases=["r"],
        default=MISSING,
    )
    expires_at: int = commands.flag(
        name="expires_at",
        description="The time in days the ban will last for.",
        aliases=["t", "d", "e", "duration", "expires", "time"],
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="The number of days (< 7) to purge in messages.",
        aliases=["p"],
        default=0,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class KickFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the kick.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TimeoutFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    duration: str = commands.flag(
        name="duration",
        description="The duration of the timeout. (e.g. 1d, 1h, 1m)",
        aliases=["d"],
        default=MISSING,
    )
    reason: str = commands.flag(
        name="reason",
        description="The reason for the timeout.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UntimeoutFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the untimeout.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnbanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    username_or_id: str = commands.flag(
        name="username_or_id",
        description="The username or ID of the user.",
        aliases=["u"],
        default=MISSING,
        positional=True,
    )
    reason: str = commands.flag(
        name="reason",
        description="The reason for the unban.",
        aliases=["r"],
        default=MISSING,
    )


class JailFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the jail.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnjailFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the unjail.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class CasesViewFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    type: CaseType = commands.flag(
        name="case_type",
        description="The case type to view.",
        aliases=["t"],
        default=None,
        converter=CaseTypeConverter,
    )
    target: discord.User = commands.flag(
        name="case_target",
        description="The user to view cases for.",
        aliases=["user", "u", "member", "memb", "m"],
        default=None,
    )
    moderator: discord.User = commands.flag(
        name="case_moderator",
        description="The moderator to view cases for.",
        aliases=["mod"],
        default=None,
    )


class CaseModifyFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    status: bool | None = commands.flag(
        name="case_status",
        description="The status of the case.",
        aliases=["s"],
    )
    reason: str | None = commands.flag(
        name="case_reason",
        description="The modified reason.",
        aliases=["r"],
    )


class WarnFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the warn.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class SnippetBanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet ban.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class SnippetUnbanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet unban.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )
