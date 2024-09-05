import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import UnjailFlags, generate_usage

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.unjail.usage = generate_usage(self.unjail, UnjailFlags)

    @commands.hybrid_command(
        name="unjail",
        aliases=["uj"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def unjail(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: UnjailFlags,
    ) -> None:
        """
        Unjail a member in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        member : discord.Member
            The member to unjail.
        flags : UnjailFlags
            The flags for the command. (reason: str, silent: bool)
        """

        assert ctx.guild

        moderator = ctx.author

        if not await self.check_conditions(ctx, member, moderator, "unjail"):
            return

        jail_role_id = await self.config.get_jail_role_id(ctx.guild.id)
        jail_role = ctx.guild.get_role(jail_role_id) if jail_role_id else None

        if not jail_role:
            await ctx.send("The jail role has been deleted or not set up.", delete_after=30, ephemeral=True)
            return

        if jail_role not in member.roles:
            await ctx.send("The member is not jailed.", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.get_last_jail_case_by_user_id(ctx.guild.id, member.id)
        if not case:
            await ctx.send("No jail case found for this member.", delete_after=30, ephemeral=True)
            return

        try:
            previous_roles = [await commands.RoleConverter().convert(ctx, str(role)) for role in case.case_user_roles]
            if previous_roles:
                await member.remove_roles(jail_role, reason=flags.reason, atomic=True)
                await member.add_roles(*previous_roles, reason=flags.reason, atomic=True)
            else:
                await ctx.send("No previous roles found for the member.", delete_after=30, ephemeral=True)
                return

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to unjail member {member}. {e}")
            await ctx.send(f"Failed to unjail member {member}. {e}", delete_after=30, ephemeral=True)
            return

        unjail_case = await self.db.case.insert_case(
            guild_id=ctx.guild.id,
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNJAIL,
            case_reason=flags.reason,
        )

        await self.handle_case_response(ctx, CaseType.UNJAIL, unjail_case.case_number, flags.reason, member)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unjail(bot))
