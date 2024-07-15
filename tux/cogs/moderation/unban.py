import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils.constants import Constants as CONST
from tux.utils.flags import UnbanFlags

from . import ModerationCogBase


class Unban(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="unban",
        aliases=["ub"],
        usage="$unban [target] [reason]",
    )
    @commands.guild_only()
    async def unban(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
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
            The flags for the command.

        Raises
        ------
        discord.Forbidden
            If the bot does not have the necessary permissions.
        discord.HTTPException
            If an error occurs while unbanning the user.
        """

        # moderator = await commands.MemberConverter().convert(ctx, str(ctx.author.id))

        # Check for necessary permissions
        if ctx.guild is None:
            logger.warning("Unban command used outside of a guild context.")
            return

        # Get the list of banned users in the guild
        banned_users = [ban.user async for ban in ctx.guild.bans()]

        try:
            # If the username_or_id is an integer, search for the user by ID
            user_id = int(flags.username_or_id)
            user_to_unban = discord.utils.get(banned_users, id=user_id)

        except ValueError:
            # If the username_or_id is not an integer, search for the user by username
            user_to_unban = discord.utils.find(lambda u: u.name == flags.username_or_id, banned_users)

        if user_to_unban is None:
            await ctx.reply("User not found or incorrect ID/username provided.", delete_after=10, ephemeral=True)
            return

        try:
            await ctx.guild.unban(user_to_unban, reason=flags.reason)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to unban {user_to_unban}. {e}")
            await ctx.reply(f"Failed to unban {user_to_unban}. {e}", delete_after=10, ephemeral=True)
            return

        case = await self.db.case.insert_case(
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNBAN,
            case_reason=flags.reason,
            guild_id=ctx.guild.id,
        )

        await self.handle_case_response(ctx, case, "created", flags.reason, target)

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
                icon_url=CONST.EMBED_ICONS["CASE"],
            )
        else:
            embed = await self.create_embed(
                ctx,
                title=f"Case {action} ({CaseType.BAN})",
                fields=fields,
                color=CONST.EMBED_COLORS["CASE"],
                icon_url=CONST.EMBED_ICONS["CASE"],
            )

        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.reply(embed=embed, delete_after=10, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unban(bot))
