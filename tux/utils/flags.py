import inspect
import random
from typing import Any

import discord
from discord.ext import commands
from discord.utils import MISSING

from prisma.enums import CaseType
from tux.utils.converters import CaseTypeConverter


def generate_usage(
    command: commands.Command[Any, Any, Any],
    flag_converter: type[commands.FlagConverter] | None = None,
) -> str:
    """
    Generate a usage string for a command with flags.

    Parameters
    ----------
    command : commands.Command
        The command for which to generate the usage string.
    flag_converter : type[commands.FlagConverter]
        The flag converter class for the command.

    Returns
    -------
    str
        The usage string for the command. Example: ">ban @target -reason [-silent | -purge_days]"
    """

    command_name = command.qualified_name
    usage = f"{command_name}"

    parameters: dict[str, commands.Parameter] = command.clean_params
    flag_prefix = getattr(flag_converter, "__commands_flag_prefix__", "-")
    flags: dict[str, commands.Flag] = flag_converter.get_flags() if flag_converter else {}

    for param_name, param in parameters.items():
        if param_name in ["ctx", "flags"]:
            continue
        is_required = param.default == inspect.Parameter.empty
        matching_string = get_matching_string(param_name)

        if matching_string == param_name and is_required:
            matching_string = f"<{param_name}>"

        usage += f" {matching_string}" if is_required else f" [{matching_string}]"

    required_flags: list[str] = []
    optional_flags: list[str] = []
    for flag_name, flag_obj in flags.items():
        flag = f"{flag_prefix}{flag_name}"
        if flag_obj.required:
            required_flags.append(flag)
        else:
            optional_flags.append(flag)

    for flag in required_flags:
        usage += f" {flag}"

    if optional_flags:
        usage += f" [{' | '.join(optional_flags)}]"

    return usage


def get_matching_string(arg: str) -> str:
    """
    Matches the given argument to a specific string based on common usage.

    Args:
      arg: The argument to match.

    Returns:
      The matching string, or None if no match is found.
    """

    match arg:
        case "user" | "target" | "member" | "name" | "username":
            return "@member"
        case "number" | "num" | "n" | "limit":
            return str(random.randint(1, 20))
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
        description="Reason for the ban.",
        aliases=["r"],
        default=MISSING,
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="Number of days in messages. (< 7)",
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
        description="Reason for the temp ban.",
        aliases=["r"],
        default=MISSING,
    )
    expires_at: int = commands.flag(
        name="duration",
        description="Number of days the ban will last for.",
        aliases=["t", "d", "e", "expires", "time"],
    )
    purge_days: int = commands.flag(
        name="purge_days",
        description="Number of days in messages. (< 7)",
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
        description="Reason for the kick.",
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
        description="Duration of the timeout. (e.g. 1d, 1h, 1m)",
        aliases=["d"],
        default=MISSING,
    )
    reason: str = commands.flag(
        name="reason",
        description="Reason for the timeout.",
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
        description="Reason for the untimeout.",
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
    reason: str = commands.flag(
        name="reason",
        description="Reason for the unban.",
        aliases=["r"],
        default=MISSING,
    )


class JailFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="Reason for the jail.",
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
        description="Reason for the unjail.",
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
        name="type",
        description="Type of case to view.",
        aliases=["t"],
        default=None,
        converter=CaseTypeConverter,
    )
    user: discord.User = commands.flag(
        name="user",
        description="User to view cases for.",
        aliases=["u", "member", "memb", "m", "target"],
        default=None,
    )
    moderator: discord.User = commands.flag(
        name="mod",
        description="Moderator to view cases for.",
        aliases=["moderator"],
        default=None,
    )


class CaseModifyFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    status: bool | None = commands.flag(
        name="status",
        description="Status of the case.",
        aliases=["s"],
    )
    reason: str | None = commands.flag(
        name="reason",
        description="Modified reason.",
        aliases=["r"],
    )


class WarnFlags(commands.FlagConverter, case_insensitive=True, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="Reason for the warn.",
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
        description="Reason for the snippet ban.",
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
        description="Reason for the snippet unban.",
        aliases=["r"],
        default=MISSING,
    )
    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )
