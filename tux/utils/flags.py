import inspect
from typing import Any, Union, get_args, get_origin

import discord
from discord.ext import commands

from prisma.enums import CaseType
from tux.utils.constants import CONST
from tux.utils.converters import CaseTypeConverter, TimeConverter, convert_bool

# TODO: Figure out how to use boolean flags with empty values


def is_optional_param(param: commands.Parameter) -> bool:
    """
    Check if a parameter is optional.

    Parameters
    ----------
    param : commands.Parameter
        The parameter to check.

    Returns
    -------
    bool
        True if the parameter is optional, False otherwise.
    """

    if param.default is not inspect.Parameter.empty:
        return True

    param_type = param.annotation

    if get_origin(param_type) is Union:
        return type(None) in get_args(param_type)

    return False


def generate_usage(
    command: commands.Command[Any, Any, Any],
    flag_converter: type[commands.FlagConverter] | None = None,
) -> str:
    """
    Generate the usage string for a command.

    Parameters
    ----------
    command : commands.Command[Any, Any, Any]
        The command to generate the usage string for.
    flag_converter : type[commands.FlagConverter] | None
        The flag converter to use.

    Returns
    -------
    str
        The usage string for the command.
    """

    command_name = command.qualified_name
    usage = f"{command_name}"

    parameters: dict[str, commands.Parameter] = command.clean_params

    flag_prefix = getattr(flag_converter, "__commands_flag_prefix__", "-")
    flags: dict[str, commands.Flag] = flag_converter.get_flags() if flag_converter else {}

    # Handle regular parameters first
    for param_name, param in parameters.items():
        if param_name in {"ctx", "flags"}:
            continue

        is_required = not is_optional_param(param)
        matching_string = get_matching_string(param_name)

        if matching_string == param_name and is_required:
            matching_string = f"<{param_name}>"

        usage += f" {matching_string}" if is_required else f" [{matching_string}]"

    # Find positional flag if it exists
    positional_flag = None
    required_flags: list[str] = []
    optional_flags: list[str] = []

    for flag_name, flag_obj in flags.items():
        if getattr(flag_obj, "positional", False):
            positional_flag = flag_name
            continue

        flag = f"{flag_prefix}{flag_name}"

        if flag_obj.required:
            required_flags.append(flag)
        else:
            optional_flags.append(flag)

    # Add positional flag in its correct position
    if positional_flag:
        usage += f" [{positional_flag}]"

    # Add required flags
    for flag in required_flags:
        usage += f" {flag}"

    # Add optional flags
    if optional_flags:
        usage += f" [{' | '.join(optional_flags)}]"

    return usage


def get_matching_string(arg: str) -> str:
    """
    Matches the given argument to a specific string based on common usage.

    Parameters
    ----------
    arg : str
        The argument to match.

    Returns
    -------
    str
        The matching string, or None if no match is found.
    """
    match arg:
        case "user" | "target" | "member" | "username":
            return "@member"
        case "search_term":
            return "CIA"
        case "channel":
            return "#general"
        case "comic_id":
            return "1337"
        case _:
            return arg


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
