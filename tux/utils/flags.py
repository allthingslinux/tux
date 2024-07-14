from discord.ext import commands


class BanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member ban.",
        aliases=["r"],
        default="No reason provided.",
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


class TempBanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    reason: str = commands.flag(
        name="reason",
        description="The reason for the member temp ban.",
        aliases=["r"],
        default="No reason provided.",
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
        default="No reason provided.",
    )

    silent: bool = commands.flag(
        name="silent",
        description="Do not send a DM to the target.",
        aliases=["s", "quiet"],
        default=False,
    )


class UnbanFlags(commands.FlagConverter, delimiter=" ", prefix="-"):
    username_or_id: int | str = commands.flag(
        name="username_or_id",
        description="The username or ID of the user to ban.",
        default=0,
    )

    reason: str = commands.flag(
        name="reason",
        description="The reason for the member ban.",
        aliases=["r"],
        default="No reason provided.",
    )
