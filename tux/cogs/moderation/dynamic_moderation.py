"""
Dynamic moderation command system.

Automatically generates moderation commands from the configuration in
`tux.cogs.moderation.command_config`.
"""

from __future__ import annotations

from typing import Any, Callable, Coroutine

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.utils import checks

from . import ModerationCogBase
from .command_config import MODERATION_COMMANDS, ModerationCommandConfig
from tux.utils.transformers import MemberOrUser


class DynamicModerationCog(ModerationCogBase):
    """Cog that registers *all* moderation commands dynamically."""

    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
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
        async def _cmd(  # type: ignore[override]
            self: "DynamicModerationCog",
            ctx: commands.Context,  # plain Context for slash compatibility
            target: MemberOrUser,
            *,
            mixed_args: str = "",
        ) -> None:  # noqa: D401, ANN001
            await self.execute_mixed_mod_action(ctx, config, target, mixed_args)

        _cmd.__name__ = config.name
        _cmd.__doc__ = config.description

        # Wrap with decorators
        command_factory: Callable[[Callable[..., Coroutine[Any, Any, None]]], commands.HybridCommand[Any]] = commands.hybrid_command(
            name=config.name,
            aliases=config.aliases,
            description=config.description,
            with_app_command=True,
        )
        cmd_obj = command_factory(_cmd)  # type: ignore[arg-type]
        cmd_obj = commands.guild_only()(cmd_obj)  # type: ignore[assignment]
        cmd_obj = checks.has_pl(config.required_permission_level)(cmd_obj)  # type: ignore[assignment]

        # Usage string for help
        cmd_obj.usage = config.get_usage_string()

        # Attach to cog instance & add to bot
        setattr(self, config.name, cmd_obj)
        self.bot.add_command(cmd_obj)


async def setup(bot: Tux) -> None:
    """Entrypoint for this cog (called by discord.py loader)."""
    await bot.add_cog(DynamicModerationCog(bot))
