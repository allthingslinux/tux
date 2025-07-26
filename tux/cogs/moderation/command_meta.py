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

        # Create the hybrid command callback
        async def _callback(self: ModerationCogBase, ctx, target: MemberOrUser, *, flags: FlagsCls = FlagsCls(), reason: str = "") -> None:  # type: ignore[override]
            # Permission / sanity checks
            if not await self.check_conditions(ctx, target, ctx.author, cmd_name):
                return

            silent = getattr(flags, "silent", False)
            duration = getattr(flags, "duration", None)
            purge = getattr(flags, "purge", 0)

            # Build coroutine list using subclass _action
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

        # Ensure eval_annotation can resolve FlagsCls
        if FlagsCls is not None:
            _callback.__globals__[FlagsCls.__name__] = FlagsCls
            _callback.__globals__['FlagsCls'] = FlagsCls  # alias for eval string
            from typing import Dict as _Dict  # noqa: WPS433
            _callback.__globals__.setdefault('Dict', _Dict)

        _callback.__name__ = cmd_name
        _callback.__doc__ = description

        cmd_obj = commands.hybrid_command(
            name=cmd_name,
            aliases=aliases,
            description=description,
            with_app_command=True,
        )(_callback)  # type: ignore[arg-type]

        # store on cls for later access
        cls.command = cmd_obj  # type: ignore[attr-defined]

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
            self.add_command(cls.command)


async def setup(bot: commands.Bot):
    # Ensure all command modules are imported so subclasses register
    import importlib
    importlib.import_module("tux.cogs.moderation.commands")

    await bot.add_cog(ModerationCommandsCog(bot))