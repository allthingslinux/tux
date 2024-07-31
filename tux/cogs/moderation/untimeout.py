import discord
from discord.ext import commands
from loguru import logger

import tux.utils.checks as checks
from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST
from tux.utils.flags import UntimeoutFlags

from . import ModerationCogBase


class Untimeout(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="untimeout",
        aliases=["ut", "uto", "unmute"],
        usage="$untimeout [target] [reason]",
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
        Untimeout a user from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The user to timeout.
        flags : UntimeoutFlags
            The flags for the command.

        Raises
        ------
        discord.DiscordException
            If an error occurs while timing out the user.
        """

        moderator = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        if ctx.guild is None:
            logger.warning("Timeout command used outside of a guild context.")
            return
        if target == ctx.author:
            await ctx.reply("You cannot untimeout yourself.", delete_after=30, ephemeral=True)
            return
        if target.top_role >= moderator.top_role:
            await ctx.reply("You cannot untimeout a user with a higher or equal role.", delete_after=30, ephemeral=True)
            return
        if target == ctx.guild.owner:
            await ctx.reply("You cannot untimeout the server owner.", delete_after=30, ephemeral=True)
            return
        if not target.is_timed_out():
            await ctx.reply(f"{target} is not currently timed out.", delete_after=30, ephemeral=True)

        try:
            await self.send_dm(ctx, flags.silent, target, flags.reason, "untimed out")
            await target.timeout(None, reason=flags.reason)
        except discord.DiscordException as e:
            await ctx.reply(f"Failed to untimeout {target}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNTIMEOUT,
            case_reason=flags.reason,
            case_expires_at=None,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, flags, case, "created", flags.reason, target)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        flags: UntimeoutFlags,
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        if case is not None:
            embed = await self.create_embed(
                ctx,
                title=f"Case #{case.case_number} {action} ({case.case_type})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )
            embed.set_thumbnail(url=target.avatar)
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case #0 {action} ({CaseType.UNTIMEOUT})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=30, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Untimeout(bot))
