from __future__ import annotations

import discord
from discord.ext import commands
from prisma.enums import CaseType

from tux.cogs.moderation.action_mixin import ModerationActionMixin
from tux.cogs.moderation.common import ModCmdInfo, mod_command
from tux.utils.transformers import MemberOrUser
from discord.ext import commands as ext_cmds


# ---------------- FlagConverter for prefix command -------------------------


class BanFlags(ext_cmds.FlagConverter, delimiter=" ", prefix="-"):  # noqa: D401
    """Flags for `>ban` command."""

    purge: int = ext_cmds.flag(
        default=0,
        aliases=["p"],
        description="Days of messages to delete (0-7)",
    )

    silent: bool = ext_cmds.flag(
        default=False,
        aliases=["s", "quiet"],
        description="Don't DM the target",
    )

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
            flags: BanFlags | None = None,
            reason: str = "",
        ) -> None:  # noqa: D401
            purge_val = flags.purge if flags else 0  # type: ignore[union-attr]
            silent_val = flags.silent if flags else False  # type: ignore[union-attr]

            await self._run_action(
                ctx,
                member=member,
                reason=reason,
                duration=None,
                purge=purge_val,
                silent=silent_val,
                case_type=BAN_INFO.case_type,
                dm_verb=BAN_INFO.dm_verb,
                discord_action=lambda: ctx.guild.ban(  # type: ignore[return-value]
                    member,
                    reason=reason,
                    delete_message_seconds=purge_val * 86_400,
                ),
            )

        # decorator returns tuple of commands
        return _ban  # type: ignore[return-value]


async def setup(bot: commands.Bot):  # noqa: D401
    await bot.add_cog(BanCog(bot))