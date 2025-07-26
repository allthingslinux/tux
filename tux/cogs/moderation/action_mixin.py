from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import discord
from discord.ext import commands
from prisma.enums import CaseType

from tux.cogs.moderation import ModerationCogBase
from tux.utils.constants import CONST
from tux.utils.transformers import MemberOrUser

__all__ = ["ModerationActionMixin"]


class ModerationActionMixin(ModerationCogBase):
    """Shared execution helper for moderation actions.

    This mixin builds the *actions* list and delegates to
    :py:meth:`ModerationCogBase.execute_mod_action` so concrete commands only
    need to supply metadata and the Discord API coroutine.
    """

    async def _run_action(  # noqa: WPS211  (many params is ok for clarity)
        self,
        ctx: commands.Context,  # noqa: D401
        *,
        member: MemberOrUser,
        reason: str,
        duration: str | None,
        purge: int,
        silent: bool,
        case_type: CaseType,
        dm_verb: str,
        discord_action: Callable[[], Awaitable[Any]] | None = None,
    ) -> None:
        """Validate and execute the moderation workflow."""

        assert ctx.guild is not None, "Guild-only command"  # noqa: S101

        # Permission / sanity checks
        if not await self.check_conditions(ctx, member, ctx.author, case_type.name.lower()):
            return

        if purge and not (0 <= purge <= 7):
            await ctx.send("Purge must be between 0 and 7 days.", ephemeral=True)
            return

        final_reason = reason or CONST.DEFAULT_REASON

        actions: list[tuple[Awaitable[Any], type[Any]]] = []
        if discord_action is not None:
            actions.append((discord_action(), type(None)))

        await self.execute_mod_action(
            ctx=ctx,
            case_type=case_type,
            user=member,
            reason=final_reason,
            silent=silent,
            dm_action=dm_verb,
            actions=actions,
            duration=duration,
        )


# ---------------------------------------------------------------------------
# No-op setup so the cog loader skips this util module
# ---------------------------------------------------------------------------


async def setup(bot):  # type: ignore[unused-argument]
    """Utility module – nothing to load."""
    return