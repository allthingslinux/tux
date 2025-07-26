from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, TypeAlias

import discord
from discord import app_commands
from discord.ext import commands
from prisma.enums import CaseType

from tux.utils.transformers import MemberOrUser

__all__ = [
    "ModCmdInfo",
    "mod_command",
]


@dataclass(slots=True, frozen=True)
class ModCmdInfo:
    """Static metadata for a moderation command."""

    name: str
    aliases: list[str]
    description: str
    case_type: CaseType
    required_pl: int
    dm_verb: str
    supports_duration: bool = False
    supports_purge: bool = False
    supports_silent: bool = True


T_Context: TypeAlias = commands.Context  # generic enough


# Signature of the wrapped coroutine (implemented in concrete cog)
WrappedFunc: TypeAlias = Callable[
    [T_Context, MemberOrUser],
    Awaitable[None],
]


def mod_command(info: ModCmdInfo):
    """Decorator that builds prefix *and* slash command versions.

    The decorated coroutine must be defined inside a subclass of
    :class:`~tux.cogs.moderation.action_mixin.ModerationActionMixin` and must
    accept the following signature::

        async def cmd(self, ctx: commands.Context, member: MemberOrUser, *,
                       duration: str | None = None, purge: int = 0,
                       silent: bool = False, reason: str = ""): ...

    Unused parameters (e.g. *duration*) can be omitted if the corresponding
    ``supports_*`` flag is *False*.
    """

    def decorator(func: Callable[..., Awaitable[None]]):
        # ---------------- prefix command ----------------
        prefix_cmd = commands.command(
            name=info.name,
            aliases=info.aliases,
            help=info.description,
        )(func)

        # Provide clean usage string (no ctx)
        prefix_cmd.usage = f"{info.name} <member> <flags> <reason>"

        # ---------------- slash command -----------------
        # Build parameters dynamically based on supports_* flags
        async def slash_callback(
            interaction: discord.Interaction,
            member: MemberOrUser,
            *,
            duration: str | None = None,
            purge: int = 0,
            silent: bool = False,
            reason: str = "",
        ) -> None:  # noqa: D401
            bot = interaction.client
            assert isinstance(bot, commands.Bot)
            ctx = await bot.get_context(interaction)
            await func(
                ctx,  # type: ignore[arg-type]
                member,
                duration=duration,
                purge=purge,
                silent=silent,
                reason=reason,
            )

        # Build the slash command object
        slash_cmd = app_commands.command(name=info.name, description=info.description)(slash_callback)

        # Attach metadata
        setattr(prefix_cmd, "mod_info", info)
        setattr(slash_cmd, "mod_info", info)

        # Return both commands so the caller can register them
        return prefix_cmd, slash_cmd

    return decorator