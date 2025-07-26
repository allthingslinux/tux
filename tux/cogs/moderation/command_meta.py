"""Metaclass + base class for declarative moderation commands.

Subclass `ModerationCommand` once per moderation action.  Example::

    class Ban(ModerationCommand):
        name = "ban"
        aliases = ["b"]
        case_type = CaseType.BAN
        required_pl = 3
        flags = {
            "purge": dict(type=int, aliases=["p"], default=0, desc="Days to delete"),
            "silent": dict(type=bool, aliases=["s", "quiet"], default=False, desc="No DM"),
        }

        async def _action(self, guild: discord.Guild, member: discord.Member, *, flags, reason):
            await guild.ban(member, reason=reason, delete_message_seconds=flags.purge * 86400)
"""
from __future__ import annotations

from typing import Any, ClassVar, Dict, Type

import discord
from discord.ext import commands

from tux.utils.flag_factory import build_flag_converter
from tux.utils.transformers import MemberOrUser
from . import ModerationCogBase  # relative import

_REGISTRY: list[Type["ModerationCommand"]] = []


class ModerationCommandMeta(type):
    """Metaclass that turns class attributes into a real command."""

    def __new__(mcls, name: str, bases: tuple[type, ...], ns: dict[str, Any]):
        cls = super().__new__(mcls, name, bases, ns)
        if cls.__name__ == "ModerationCommand":
            return cls

        # Extract required attributes
        cmd_name: str = getattr(cls, "name")  # type: ignore[arg-type]
        aliases: list[str] = getattr(cls, "aliases", [])  # type: ignore[arg-type]
        case_type = getattr(cls, "case_type")
        required_pl: int = getattr(cls, "required_pl", 0)
        flags_spec: Dict[str, Dict[str, Any]] = getattr(cls, "flags", {})  # type: ignore[arg-type]
        description: str = getattr(cls, "description", cmd_name.title())

        # Build FlagConverter
        FlagsCls = build_flag_converter(
            cmd_name,
            duration="duration" in flags_spec,
            purge="purge" in flags_spec,
            silent="silent" in flags_spec,
        )

        # --------------------------------------------------
        # Shared executor
        # --------------------------------------------------
        async def _run(self: ModerationCogBase, ctx, target: MemberOrUser, flags, reason: str):
            if not await self.check_conditions(ctx, target, ctx.author, cmd_name):
                return

            silent = getattr(flags, "silent", False)
            duration = getattr(flags, "duration", None)

            action_coro = cls._action(self, ctx.guild, target, flags=flags, reason=reason)  # type: ignore[arg-type]
            actions = [(action_coro, type(None))]

            await self.execute_mod_action(
                ctx=ctx,
                case_type=case_type,
                user=target,
                reason=reason,
                silent=silent,
                dm_action=getattr(cls, "dm_action", cmd_name),
                actions=actions,
                duration=duration,
            )

        # --------------------------------------------------
        # Text command (prefix)
        # --------------------------------------------------
        async def _text(self: ModerationCogBase, ctx: commands.Context, target: MemberOrUser, *, flags: FlagsCls | None = None, reason: str = "") -> None:  # type: ignore[arg-type]
            if flags is None:
                flags = FlagsCls()  # type: ignore[assignment]
            await _run(self, ctx, target, flags, reason)

        if FlagsCls is not None:
            _text.__globals__[FlagsCls.__name__] = FlagsCls
            from typing import Dict as _Dict
            _text.__globals__.setdefault('Dict', _Dict)

        _text.__name__ = cmd_name
        _text.__doc__ = description

        text_cmd = commands.command(name=cmd_name, aliases=aliases, help=description)(_text)

        # --------------------------------------------------
        # Slash command
        # --------------------------------------------------
        async def _slash(self: ModerationCogBase, interaction: discord.Interaction, target: MemberOrUser, *, flags: FlagsCls | None = None, reason: str = "") -> None:  # type: ignore[arg-type]
            if flags is None:
                flags = FlagsCls()  # type: ignore[assignment]
            ctx = await self.bot.get_context(interaction)  # type: ignore[attr-defined]
            await _run(self, ctx, target, flags, reason)

        if FlagsCls is not None:
            _slash.__globals__[FlagsCls.__name__] = FlagsCls

        slash_cmd = discord.app_commands.command(name=cmd_name, description=description)(_slash)

        # store on cls
        cls.text_command = text_cmd  # type: ignore[attr-defined]
        cls.slash_command = slash_cmd  # type: ignore[attr-defined]

        # register class
        _REGISTRY.append(cls)
        return cls


class ModerationCommand(metaclass=ModerationCommandMeta):
    """Base class to inherit for each moderation action."""

    name: ClassVar[str]
    aliases: ClassVar[list[str]] = []
    case_type: ClassVar[Any]
    required_pl: ClassVar[int] = 0
    flags: ClassVar[Dict[str, Dict[str, Any]]] = {}
    description: ClassVar[str] = ""

    # Child classes must implement _action
    async def _action(self, guild: discord.Guild, member: discord.Member | discord.User, *, flags: Any, reason: str) -> None:  # noqa: D401
        raise NotImplementedError


# Cog that loads all ModerationCommand subclasses
class ModerationCommandsCog(ModerationCogBase):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)  # type: ignore[arg-type]

        for cls in _REGISTRY:
            self.bot.add_command(cls.text_command)  # type: ignore[attr-defined]
            self.bot.tree.add_command(cls.slash_command)  # type: ignore[attr-defined]


async def setup(bot: commands.Bot):
    # Ensure all command modules are imported so subclasses register
    import importlib
    importlib.import_module("tux.cogs.moderation.commands")

    await bot.add_cog(ModerationCommandsCog(bot))