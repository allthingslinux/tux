from __future__ import annotations

import discord
from discord.ext import commands
from prisma.enums import CaseType

from tux.cogs.moderation.action_mixin import ModerationActionMixin
from tux.cogs.moderation.common import ModCmdInfo, mod_command
from tux.utils.transformers import MemberOrUser

BAN_INFO = ModCmdInfo(
    name="ban",
    aliases=["b"],
    description="Ban a member from the server.",
    case_type=CaseType.BAN,
    required_pl=3,
    dm_verb="banned",
    supports_purge=True,
)


class BanCog(ModerationActionMixin, commands.Cog):
    """Ban command implemented with explicit definition."""

    def __init__(self, bot: commands.Bot) -> None:  # noqa: D401
        super().__init__(bot)  # type: ignore[misc]
        # Register commands returned by decorator
        prefix_cmd, slash_cmd = self._create_commands()
        bot.add_command(prefix_cmd)
        bot.tree.add_command(slash_cmd)

    # ------------------------------------------------------------------
    # Command definitions
    # ------------------------------------------------------------------

    def _create_commands(self):  # noqa: D401
        @mod_command(BAN_INFO)
        async def _ban(
            self: BanCog,
            ctx: commands.Context,
            member: MemberOrUser,
            *,
            purge: int = 0,
            silent: bool = False,
            reason: str = "",
        ) -> None:  # noqa: D401
            await self._run_action(
                ctx,
                member=member,
                reason=reason,
                duration=None,
                purge=purge,
                silent=silent,
                case_type=BAN_INFO.case_type,
                dm_verb=BAN_INFO.dm_verb,
                discord_action=lambda: ctx.guild.ban(  # type: ignore[return-value]
                    member,
                    reason=reason,
                    delete_message_seconds=purge * 86_400,
                ),
            )

        # decorator returns tuple of commands
        return _ban  # type: ignore[return-value]


async def setup(bot: commands.Bot):  # noqa: D401
    await bot.add_cog(BanCog(bot))