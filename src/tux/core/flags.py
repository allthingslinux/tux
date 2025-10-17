import discord
from discord.ext import commands

from tux.core.converters import CaseTypeConverter, TimeConverter, convert_bool
from tux.database.models import CaseType
from tux.shared.constants import CONST


# Based on https://github.com/DuckBot-Discord/DuckBot/blob/acf762485815e2298479ad3cb1ab8f290b35e2a2/utils/converters.py#L419
class TuxFlagConverter(commands.FlagConverter):
    """A commands.FlagConverter but that supports Boolean flags with empty body.

    Parameters
    ----------
    commands : commands.FlagConverter
        The base flag converter.

    Returns
    -------
    TuxFlagConverter
        The Tux flag converter.

    Raises
    ------
    commands.MissingFlagArgument
        If a flag is missing.
    commands.TooManyArguments
        If too many arguments are passed.
    """

    @classmethod
    def parse_flags(cls, argument: str, *, ignore_extra: bool = True) -> dict[str, list[str]]:  # noqa: PLR0912, PLR0915
        result: dict[str, list[str]] = {}
        flags = cls.__commands_flags__
        aliases = cls.__commands_flag_aliases__
        positional_flag = getattr(cls, "__commands_flag_positional__", None)
        last_position = 0
        last_flag: commands.Flag | None = None

        # Normalise: allow trailing boolean flags without a space (e.g. "-silent")
        working_argument = argument if argument.endswith(" ") else argument + " "

        case_insensitive = cls.__commands_flag_case_insensitive__

        # Handle positional flag (content before first flag token)
        if positional_flag is not None:
            match = cls.__commands_flag_regex__.search(working_argument)
            if match is not None:
                begin, end = match.span(0)
                value = argument[:begin].strip()
            else:
                value = argument.strip()
                last_position = len(working_argument)

            if value:
                name = positional_flag.name.casefold() if case_insensitive else positional_flag.name
                result[name] = [value]

        for match in cls.__commands_flag_regex__.finditer(working_argument):
            begin, end = match.span(0)
            key = match.group("flag")
            if case_insensitive:
                key = key.casefold()

            if key in aliases:
                key = aliases[key]

            flag = flags.get(key)
            if last_position and last_flag is not None:
                value = working_argument[last_position : begin - 1].lstrip()
                if not value:
                    # If previous flag is boolean and has no explicit value, treat as True
                    if last_flag and last_flag.annotation is bool:
                        value = "True"
                    else:
                        raise commands.MissingFlagArgument(last_flag)

                name = last_flag.name.casefold() if case_insensitive else last_flag.name

                try:
                    values = result[name]
                except KeyError:
                    result[name] = [value]
                else:
                    values.append(value)

            last_position = end
            last_flag = flag

        # Get the remaining string, if applicable
        value = working_argument[last_position:].strip()

        # Add the remaining string to the last available flag
        if last_flag is not None:
            if not value:
                # Trailing boolean flag without value -> True
                if last_flag and last_flag.annotation is bool:
                    value = "True"
                else:
                    raise commands.MissingFlagArgument(last_flag)

            name = last_flag.name.casefold() if case_insensitive else last_flag.name

            try:
                values = result[name]
            except KeyError:
                result[name] = [value]
            else:
                values.append(value)
        elif value and not ignore_extra:
            # If we're here then we passed extra arguments that aren't flags
            msg = f"Too many arguments passed to {cls.__name__}"
            raise commands.TooManyArguments(msg)

        # Verification of values will come at a later stage
        return result


class BanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class TempBanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class UnbanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    pass


class KickFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class WarnFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class TimeoutFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class UntimeoutFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class JailFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class UnjailFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class CasesViewFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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


class CaseModifyFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    status: bool | None = commands.flag(
        name="status",
        description="Status of the case.",
        aliases=["s"],
        default=None,
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


class SnippetBanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class SnippetUnbanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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


class PollBanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class PollUnbanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
    )


class TldrFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
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
