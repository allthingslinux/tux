import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.flags import UnjailFlags

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="unjail",
        aliases=["uj"],
        usage="$unjail [target] [reason] <silent>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def unjail(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: UnjailFlags,
    ) -> None:
        """
        Unjail a user in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        target : discord.Member
            The member to unjail.
        flags : UnjailFlags
            The flags for the command. (reason: str, silent: bool)
        """
        moderator = ctx.author

        if not ctx.guild:
            logger.warning("Unjail command used outside of a guild context.")
            return

        if await self._cannot_unjail(ctx, target, moderator):
            return

        jail_role = await self._get_jail_role(ctx)
        if not jail_role:
            return
        if jail_role not in target.roles:
            await ctx.send("The user is not jailed.", delete_after=30, ephemeral=True)
            return

        if not await self._check_jail_channel(ctx):
            return

        case = await self.db.case.get_last_jail_case_by_target_id(ctx.guild.id, target.id)
        if not case:
            await ctx.send("No jail case found for the user.", delete_after=30, ephemeral=True)
            return

        await self._unjail_user(ctx, target, jail_role, case, flags.reason)

        unjail_case = await self._insert_unjail_case(ctx, target, flags.reason)

        await self.handle_case_response(ctx, unjail_case, "created", flags.reason, target)

    async def _cannot_unjail(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        moderator: discord.Member | discord.User,
    ) -> bool:
        if ctx.guild is None:
            logger.warning("Unjail command used outside of a guild context.")
            return True

        if target == ctx.author:
            await ctx.send("You cannot unjail yourself.", delete_after=30, ephemeral=True)
            return True

        if isinstance(moderator, discord.Member) and target.top_role >= moderator.top_role:
            await ctx.send("You cannot unjail a user with a higher or equal role.", delete_after=30, ephemeral=True)
            return True

        if target == ctx.guild.owner:
            await ctx.send("You cannot unjail the server owner.", delete_after=30, ephemeral=True)
            return True

        return False

    async def _get_jail_role(self, ctx: commands.Context[commands.Bot]) -> discord.Role | None:
        if ctx.guild is None:
            logger.warning("Unjail command used outside of a guild context.")
            return None

        jail_role_id = await self.config.get_jail_role(ctx.guild.id)
        if not jail_role_id:
            await ctx.send("No jail role has been set up for this server.", delete_after=30, ephemeral=True)
            return None

        jail_role = ctx.guild.get_role(jail_role_id)
        if not jail_role:
            await ctx.send("The jail role has been deleted.", delete_after=30, ephemeral=True)
            return None

        return jail_role

    async def _check_jail_channel(self, ctx: commands.Context[commands.Bot]) -> bool:
        if ctx.guild is None:
            logger.warning("Unjail command used outside of a guild context.")
            return False

        jail_channel_id = await self.config.get_jail_channel(ctx.guild.id)
        if not jail_channel_id:
            await ctx.send("No jail channel has been set up for this server.", delete_after=30, ephemeral=True)
            return False

        return True

    async def _unjail_user(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        jail_role: discord.Role,
        case: Case,
        reason: str,
    ) -> None:
        if ctx.guild is None:
            logger.warning("Unjail command used outside of a guild context.")
            return

        try:
            await target.remove_roles(jail_role, reason=reason)

            previous_roles = [await commands.RoleConverter().convert(ctx, str(role)) for role in case.case_target_roles]

            if previous_roles:
                await target.add_roles(*previous_roles, reason=reason, atomic=False)
            else:
                await ctx.send("No previous roles found for the user.", delete_after=30, ephemeral=True)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to unjail user {target}. {e}")
            await ctx.send(f"Failed to unjail user {target}. {e}", delete_after=30, ephemeral=True)

    async def _insert_unjail_case(
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        reason: str,
    ) -> Case | None:
        if not ctx.guild:
            logger.warning("Unjail command used outside of a guild context.")
            return None

        try:
            return await self.db.case.insert_case(
                guild_id=ctx.guild.id,
                case_target_id=target.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.UNJAIL,
                case_reason=reason,
            )

        except Exception as e:
            logger.error(f"Failed to insert unjail case for {target}. {e}")
            await ctx.send(f"Failed to insert unjail case for {target}. {e}", delete_after=30, ephemeral=True)
            return None

    async def handle_case_response(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        reason: str,
        target: discord.Member | discord.User,
        previous_reason: str | None = None,
    ) -> None:
        fields = [
            ("Moderator", f"__{ctx.author}__\n`{ctx.author.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Reason", f"> {reason}", False),
        ]

        if previous_reason:
            fields.append(("Previous Reason", f"> {previous_reason}", False))

        embed = await self._create_case_embed(ctx, case, action, fields, target)
        await self.send_embed(ctx, embed, log_type="mod")
        await ctx.send(embed=embed, delete_after=30, ephemeral=True)

    async def _create_case_embed(
        self,
        ctx: commands.Context[commands.Bot],
        case: Case | None,
        action: str,
        fields: list[tuple[str, str, bool]],
        target: discord.Member | discord.User,
    ) -> discord.Embed:
        title = (
            f"Case #{case.case_number} ({case.case_type}) {action}" if case else f"Case {action} ({CaseType.UNJAIL})"
        )

        embed = await self.create_embed(
            ctx,
            title=title,
            fields=fields,
            color=CONST.EMBED_COLORS["CASE"],
            icon_url=CONST.EMBED_ICONS["ACTIVE_CASE"],
        )

        embed.set_thumbnail(url=target.avatar)
        return embed


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unjail(bot))
