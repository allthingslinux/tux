"""
Dynamic moderation command system.

Automatically generates moderation commands from the configuration in
`tux.cogs.moderation.command_config`.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.utils import checks

from . import ModerationCogBase
from .command_config import MODERATION_COMMANDS, ModerationCommandConfig
from tux.utils.transformers import MemberOrUser
# from tux.utils.mixed_args import generate_mixed_usage, parse_mixed_arguments (deprecated)
from tux.utils.flag_factory import build_flag_converter


class DynamicModerationCog(ModerationCogBase):
    """Cog that registers *all* moderation commands dynamically."""

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        # Clean up any previously registered commands with the same names/aliases
        for cfg in MODERATION_COMMANDS.values():
            for alias in (cfg.name, *cfg.aliases):
                if bot.get_command(alias):
                    bot.remove_command(alias)

        self._register_all_commands()

    # ------------------------------------------------------------------
    # Dynamic command creator
    # ------------------------------------------------------------------
    def _register_all_commands(self) -> None:
        for config in MODERATION_COMMANDS.values():
            self._create_and_register(config)

    def _create_and_register(self, config: ModerationCommandConfig) -> None:
        """Create a command function for *config* and add it to the cog/bot."""

        # Parameter annotation choice is runtime-only; using Any avoids evaluation issues
        cog_self = self  # capture for closure

        # --------------------------------------------------------------
        # Build FlagConverter using helper
        # --------------------------------------------------------------
        FlagsCls = build_flag_converter(
            config.name,
            duration=config.supports_duration,
            purge=config.supports_purge,
            silent=config.supports_silent,
        )

        # Make sure help introspection can resolve the class via this module's globals
        if FlagsCls is not None and FlagsCls.__name__ not in globals():
            globals()[FlagsCls.__name__] = FlagsCls
            # Ensure typing aliases used in annotations are resolvable
            from typing import Dict as _Dict  # noqa: WPS433 (runtime import)
            if 'Dict' not in globals():
                globals()['Dict'] = _Dict
            import builtins as _builtins  # noqa: WPS433
            if not hasattr(_builtins, 'Dict'):
                setattr(_builtins, 'Dict', _Dict)

        # --------------------------------------------------------------
        # Define the command callback, optionally including the *flags* param
        # --------------------------------------------------------------
        if FlagsCls is not None:

            async def _cmd(  # type: ignore[override]
                ctx: commands.Context,
                target: MemberOrUser,
                *,
                flags: FlagsCls = FlagsCls(),
                reason: str = "",
            ) -> None:  # noqa: D401, ANN001
                await cog_self.execute_flag_mod_action(ctx, config, target, flags, reason)

            _cmd.__annotations__["flags"] = FlagsCls  # type: ignore[index]

        else:

            async def _cmd(  # type: ignore[override]
                ctx: commands.Context,
                target: MemberOrUser,
                *,
                reason: str = "",
            ) -> None:  # noqa: D401, ANN001
                await cog_self.execute_flag_mod_action(ctx, config, target, None, reason)

        _cmd.__name__ = config.name
        _cmd.__doc__ = config.description

        # Wrap with decorators
        command_factory: Callable[[Callable[..., Coroutine[Any, Any, None]]], commands.HybridCommand[Any]] = commands.hybrid_command(
            name=config.name,
            aliases=config.aliases,
            description=config.description,
            help=config.get_help_text(),
            with_app_command=True,
        )
        # Build the command
        cmd_obj = command_factory(_cmd)  # type: ignore[arg-type]

        # Apply decorators *in place* so we don't lose object identity
        commands.guild_only()(cmd_obj)
        checks.has_pl(config.required_permission_level)(cmd_obj)

        # Usage & docs for help system
        cmd_obj.usage = config.get_usage_string()
        cmd_obj.help = config.get_help_text()

        # Link the command back to this cog instance
        cmd_obj.cog = self  # type: ignore[attr-defined]
        setattr(self, config.name, cmd_obj)
        # Add to cog command registry so help command can discover it
        existing_cmds = list(getattr(self, "__cog_commands__", ()))  # type: ignore[attr-defined]
        existing_cmds.append(cmd_obj)
        self.__cog_commands__ = tuple(existing_cmds)  # type: ignore[attr-defined]
        # Do NOT add to bot here; commands will be registered when the cog is injected.


async def setup(bot: Tux) -> None:
    """Entrypoint for this cog (called by discord.py loader)."""
    # Use override=True so any previously registered commands with the same
    # names or aliases (e.g. from a failed reload) are replaced cleanly.
    await bot.add_cog(DynamicModerationCog(bot), override=True)
