import discord
from discord.ext import commands
from utils.constants import CONST
from utils.converters import CaseTypeConverter, TimeConverter, convert_bool

from prisma.enums import CaseType

# TODO: Figure out how to use boolean flags with empty values


class BanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the ban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    purge: commands.Range[int, 0, 7] = commands.flag(
        name="purge",
        description="Days of messages to delete (0-7).",
        aliases=["p"],
        default=0,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class TempBanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the ban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    duration: float = commands.flag(
        name="duration",
        description="Length of the ban (e.g. 1d, 1h).",
        aliases=["t", "d", "e"],
        converter=TimeConverter,
    )
    purge: commands.Range[int, 0, 7] = commands.flag(
        name="purge",
        description="Days of messages to delete (0-7).",
        aliases=["p"],
        default=0,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class UnbanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    pass


class KickFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the kick.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class WarnFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the warning.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class TimeoutFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the timeout.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    duration: str = commands.flag(
        name="duration",
        description="Length of the timeout. (e.g. 1d, 1h)",
        aliases=["t", "d", "e"],
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class UntimeoutFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the timeout.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class JailFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the jail.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class UnjailFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the jail.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class CasesViewFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    type: CaseType | None = commands.flag(
        name="type",
        description="Type of case to view.",
        aliases=["t"],
        default=None,
        converter=CaseTypeConverter,
    )
    user: discord.User | None = commands.flag(
        name="user",
        description="User to view cases for.",
        aliases=["u"],
        default=None,
    )
    moderator: discord.User | None = commands.flag(
        name="mod",
        description="Moderator to view cases for.",
        aliases=["m"],
        default=None,
    )

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        if not hasattr(self, "type"):
            self.type = None
        if not hasattr(self, "user"):
            self.user = None
        if not hasattr(self, "moderator"):
            self.moderator = None


class CaseModifyFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    status: bool | None = commands.flag(
        name="status",
        description="Status of the case.",
        aliases=["s"],
        default=None,
        converter=convert_bool,
    )
    reason: str | None = commands.flag(
        name="reason",
        description="Modified reason.",
        aliases=["r"],
        default=None,
    )

    def __init__(self):
        if all(value is None for value in (self.status, self.reason)):
            msg = "Status or reason must be provided."
            raise commands.FlagError(msg)


class SnippetBanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet ban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class SnippetUnbanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet unban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class PollBanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the poll ban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class PollUnbanFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the poll unban.",
        default=CONST.DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
        converter=convert_bool,
    )


class TldrFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    platform: str | None = commands.flag(
        name="platform",
        description="Platform (e.g. linux, osx, common)",
        aliases=["p"],
        default=None,
    )
    language: str | None = commands.flag(
        name="language",
        description="Language code (e.g. en, es, fr)",
        aliases=["lang", "l"],
        default=None,
    )
    show_short: bool = commands.flag(
        name="show_short",
        description="Display shortform options over longform.",
        aliases=["short"],
        default=False,
    )
    show_long: bool = commands.flag(
        name="show_long",
        description="Display longform options over shortform.",
        aliases=["long"],
        default=True,
    )
    show_both: bool = commands.flag(
        name="show_both",
        description="Display both short and long options.",
        aliases=["both"],
        default=False,
    )
