import asyncio

import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import WarnFlags, generate_usage

from . import ModerationCogBase


class Warn(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.warn.usage = generate_usage(self.warn, WarnFlags)

    @commands.hybrid_command(
        name="warn",
        aliases=["w"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def warn(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        reason: str | None = None,
        *,
        flags: WarnFlags,
    ) -> None:
        """
        Warn a member from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to warn.
        reason : str | None
            The reason for the warning.
        flags : WarnFlags | None
            The flags for the command. (silent: bool)
        """

        assert ctx.guild
        await ctx.defer(ephemeral=True)

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "warn"):
            return

        final_reason = reason or "No reason provided"
        silent = flags.silent if flags else False

        try:
            # Insert case and send DM concurrently
            case, dm_sent = await asyncio.gather(
                self.db.case.insert_case(
                    case_user_id=member.id,
                    case_moderator_id=ctx.author.id,
                    case_type=CaseType.WARN,
                    case_reason=final_reason,
                    guild_id=ctx.guild.id,
                ),
                self.send_dm(ctx, silent, member, final_reason, "warned"),
            )
        except Exception as e:
            logger.error(f"Failed to warn {member}. {e}")
            await ctx.send(f"Failed to warn {member}. {e}", ephemeral=True)
            return

        await self.handle_case_response(ctx, CaseType.WARN, case.case_number, final_reason, member, dm_sent)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Warn(bot))
