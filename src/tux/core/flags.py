"""Flag converters for Discord bot commands.

This module provides specialized flag converters for various moderation and utility
commands, extending discord.py's flag system with enhanced boolean handling and
case-insensitive parsing.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.converters import CaseTypeConverter, TimeConverter, convert_bool
from tux.database.models import CaseType
from tux.shared.constants import DEFAULT_REASON

__all__ = [
    # Base converter
    "TuxFlagConverter",
    # Moderation flags
    "BanFlags",
    "TempBanFlags",
    "UnbanFlags",
    "KickFlags",
    "WarnFlags",
    "TimeoutFlags",
    "UntimeoutFlags",
    "JailFlags",
    "UnjailFlags",
    # Case management flags
    "CasesViewFlags",
    "CaseModifyFlags",
    # Snippet flags
    "SnippetBanFlags",
    "SnippetUnbanFlags",
    # Poll flags
    "PollBanFlags",
    "PollUnbanFlags",
    # Utility flags
    "TldrFlags",
]


class TuxFlagConverter(commands.FlagConverter):
    """Enhanced flag converter with improved boolean flag handling.

    Extends discord.py's FlagConverter to support boolean flags with empty body
    (e.g., "-silent" becomes "-silent True"). Based on DuckBot's implementation.

    Notes
    -----
    Based on https://github.com/DuckBot-Discord/DuckBot/blob/acf762485815e2298479ad3cb1ab8f290b35e2a2/utils/converters.py#L419
    """

    @classmethod
    def parse_flags(  # noqa: PLR0912, PLR0915
        cls,
        argument: str,
        *,
        ignore_extra: bool = True,
    ) -> dict[str, list[str]]:  # sourcery skip: low-code-quality
        """Parse command arguments into flags with enhanced boolean handling.

        Extends discord.py's flag parsing to handle trailing boolean flags without
        explicit values (e.g., "-silent" becomes "-silent True").

        Parameters
        ----------
        argument : str
            The raw argument string to parse.
        ignore_extra : bool, optional
            Whether to ignore extra arguments that aren't flags. Defaults to True.

        Returns
        -------
        dict[str, list[str]]
            Dictionary mapping flag names to lists of their values.

        Raises
        ------
        commands.MissingFlagArgument
            If a required flag argument is missing.
        commands.TooManyArguments
            If too many arguments are provided when ignore_extra is False.
        """
        result: dict[str, list[str]] = {}
        flags = cls.__commands_flags__
        aliases = cls.__commands_flag_aliases__
        positional_flag = getattr(cls, "__commands_flag_positional__", None)
        last_position = 0
        last_flag: commands.Flag | None = None

        # Normalise: allow trailing boolean flags without a space (e.g. "-silent")
        working_argument = argument if argument.endswith(" ") else f"{argument} "

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
                name = (
                    positional_flag.name.casefold()
                    if case_insensitive
                    else positional_flag.name
                )
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
                        logger.debug(
                            f"Missing argument for flag: {last_flag.name if last_flag else 'unknown'}",
                        )
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
                    logger.debug(
                        f"Missing argument for trailing flag: {last_flag.name if last_flag else 'unknown'}",
                    )
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
            logger.warning(
                f"Too many arguments passed to {cls.__name__}: {value[:50]}...",
            )
            msg = f"Too many arguments passed to {cls.__name__}"
            raise commands.TooManyArguments(msg)

        # Verification of values will come at a later stage
        return result


class BanFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for ban commands.

    Attributes
    ----------
    reason : str
        The reason for the ban (positional argument).
    purge : int
        Days of messages to delete (0-7).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the ban.",
        default=DEFAULT_REASON,
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
    """Flags for temporary ban commands.

    Attributes
    ----------
    reason : str
        The reason for the ban (positional argument).
    duration : float
        Length of the ban in seconds.
    purge : int
        Days of messages to delete (0-7).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the ban.",
        default=DEFAULT_REASON,
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
    """Flags for unban commands."""


class KickFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for kick commands.

    Attributes
    ----------
    reason : str
        The reason for the kick (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the kick.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class WarnFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for warn commands.

    Attributes
    ----------
    reason : str
        The reason for the warning (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the warning.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TimeoutFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for timeout commands.

    Attributes
    ----------
    reason : str
        The reason for the timeout (positional argument).
    duration : str
        Length of the timeout (e.g. 1d, 1h).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the timeout.",
        default=DEFAULT_REASON,
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


class UntimeoutFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for untimeout commands.

    Attributes
    ----------
    reason : str
        The reason for the timeout removal (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the timeout.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class JailFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for jail commands.

    Attributes
    ----------
    reason : str
        The reason for the jail (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the jail.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnjailFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for unjail commands.

    Attributes
    ----------
    reason : str
        The reason for the jail removal (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the jail.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class CasesViewFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for viewing cases.

    Attributes
    ----------
    type : CaseType | None
        Type of case to view.
    user : discord.User | None
        User to view cases for.
    moderator : discord.User | None
        Moderator to view cases for.
    """

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
        """Initialize CasesViewFlags with default values for None attributes.

        Ensures type, user, and moderator attributes are set to None if not
        provided during initialization.
        """
        super().__init__(*args, **kwargs)
        if not hasattr(self, "type"):
            self.type = None
        if not hasattr(self, "user"):
            self.user = None
        if not hasattr(self, "moderator"):
            self.moderator = None


class CaseModifyFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for modifying cases.

    Attributes
    ----------
    status : bool | None
        Status of the case.
    reason : str | None
        Modified reason.
    """

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

    def __init__(self) -> None:
        """Initialize CaseModifyFlags and validate that at least one field is provided.

        Raises
        ------
        commands.FlagError
            If neither status nor reason is provided.
        """
        if all(value is None for value in (self.status, self.reason)):
            msg = "Status or reason must be provided."
            raise commands.FlagError(msg)


class SnippetBanFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for snippet ban commands.

    Attributes
    ----------
    reason : str
        The reason for the snippet ban (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet ban.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class SnippetUnbanFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for snippet unban commands.

    Attributes
    ----------
    reason : str
        The reason for the snippet unban (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the snippet unban.",
        default=DEFAULT_REASON,
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
    """Flags for poll ban commands.

    Attributes
    ----------
    reason : str
        The reason for the poll ban (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the poll ban.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class PollUnbanFlags(
    TuxFlagConverter,
    case_insensitive=True,
    delimiter=" ",
    prefix="-",
):
    """Flags for poll unban commands.

    Attributes
    ----------
    reason : str
        The reason for the poll unban (positional argument).
    silent : bool
        Don't send a DM to the target.
    """

    reason: str = commands.flag(
        name="reason",
        description="The reason for the poll unban.",
        default=DEFAULT_REASON,
        positional=True,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Don't send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class TldrFlags(TuxFlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    """Flags for tldr commands.

    Attributes
    ----------
    platform : str | None
        Platform (e.g. linux, osx, common).
    language : str | None
        Language code (e.g. en, es, fr).
    show_short : bool
        Display shortform options over longform.
    show_long : bool
        Display longform options over shortform.
    show_both : bool
        Display both short and long options.
    """

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
