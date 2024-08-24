import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.flags import UnbanFlags

from . import ModerationCogBase


class Unban(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="unban",
        aliases=["ub"],
        usage="unban [username_or_id] [reason]",
    )
    @commands.guild_only()
    @checks.has_pl(3)
    async def unban(
        self,
        ctx: commands.Context[commands.Bot],
        *,
        flags: UnbanFlags,
    ) -> None:
        """
        Unban a user from the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        target : discord.Member
            The member to unban.
        flags : UnbanFlags
            The flags for the command (username_or_id: str, reason: str).

        Raises
        ------
        discord.Forbidden
            If the bot does not have the necessary permissions.
        discord.HTTPException
            If an error occurs while unbanning the user.
        """

        if ctx.guild is None:
            logger.warning("Unban command used outside of a guild context.")
            return

        # Get the list of banned users in the guild
        banned_users = [ban.user async for ban in ctx.guild.bans()]
        user = await commands.UserConverter().convert(ctx, flags.username_or_id)

        if user not in banned_users:
            await ctx.send(f"{user} was not found in the guild ban list.", delete_after=30, ephemeral=True)
            return

        try:
            await ctx.guild.unban(user, reason=flags.reason)

        except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
            logger.error(f"Failed to unban {user}. {e}")
            await ctx.send(f"Failed to unban {user}. {e}", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            guild_id=ctx.guild.id,
            case_target_id=user.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNBAN,
            case_reason=flags.reason,
        )

        await self.handle_case_response(ctx, case, "created", flags.reason, user)

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
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
                title=f"Case #{case.case_number} ({case.case_type}) {action}",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )
            embed.set_thumbnail(url=target.avatar)
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case {action} ({CaseType.UNBAN})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unban(bot))
