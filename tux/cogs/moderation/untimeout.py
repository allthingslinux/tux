import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import UntimeoutFlags, generate_usage

from . import ModerationCogBase


class Untimeout(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.untimeout.usage = generate_usage(self.untimeout, UntimeoutFlags)

    @commands.hybrid_command(
        name="untimeout",
        aliases=["ut", "uto", "unmute"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def untimeout(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: UntimeoutFlags,
    ) -> None:
        """
        Untimeout a member from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to untimeout.
        flags : UntimeoutFlags
            The flags for the command (reason: str, silent: bool).

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """
        if ctx.guild is None:
            logger.warning("Timeout command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "untimeout"):
            return

        if not target.is_timed_out():
            await ctx.send(f"{target} is not currently timed out.", delete_after=30, ephemeral=True)

        try:
            await target.timeout(None, reason=flags.reason)
        except discord.DiscordException as e:
            await ctx.send(f"Failed to untimeout {target}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNTIMEOUT,
            case_reason=flags.reason,
            case_expires_at=None,
            guild_id=ctx.guild.id,
        )

        await self.send_dm(ctx, flags.silent, target, flags.reason, "untimed out")
        await self.handle_case_response(ctx, CaseType.UNTIMEOUT, case.case_id, flags.reason, target)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Untimeout(bot))
