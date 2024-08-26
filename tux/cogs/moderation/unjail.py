import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import UnjailFlags, generate_usage

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.unjail.usage = generate_usage(self.unjail, UnjailFlags)

    @commands.hybrid_command(
        name="unjail",
        aliases=["uj"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def unjail(  # noqa: PLR0911
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: UnjailFlags,
    ) -> None:
        """
        Unjail a member in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        target : discord.Member
            The member to unjail.
        flags : UnjailFlags
            The flags for the command. (reason: str, silent: bool)
        """

        if not ctx.guild:
            logger.warning("Unjail command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "unjail"):
            return

        jail_role_id = await self.config.get_jail_role_id(ctx.guild.id)
        jail_role = ctx.guild.get_role(jail_role_id) if jail_role_id else None

        jail_channel_id = await self.config.get_jail_channel_id(ctx.guild.id)

        if not all([jail_role_id, jail_role, jail_channel_id]):
            error_msgs = {
                not jail_role_id: "No jail role has been set up for this server.",
                not jail_role: "The jail role has been deleted.",
                not jail_channel_id: "No jail channel has been set up for this server.",
            }

            for condition, msg in error_msgs.items():
                if condition:
                    await ctx.send(msg, delete_after=30, ephemeral=True)
            return

        if jail_role not in target.roles:
            await ctx.send("The member is not jailed.", delete_after=30, ephemeral=True)
            return

        case = await self.db.case.get_last_jail_case_by_target_id(ctx.guild.id, target.id)
        if not case:
            await ctx.send("No jail case found for this member.", delete_after=30, ephemeral=True)
            return

        try:
            previous_roles = [await commands.RoleConverter().convert(ctx, str(role)) for role in case.case_target_roles]
            if previous_roles:
                await target.remove_roles(jail_role, reason=flags.reason, atomic=True)
                await target.add_roles(*previous_roles, reason=flags.reason, atomic=True)
            else:
                await ctx.send("No previous roles found for the member.", delete_after=30, ephemeral=True)
                return

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to unjail member {target}. {e}")
            await ctx.send(f"Failed to unjail member {target}. {e}", delete_after=30, ephemeral=True)
            return

        unjail_case = await self.db.case.insert_case(
            guild_id=ctx.guild.id,
            case_target_id=target.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNJAIL,
            case_reason=flags.reason,
        )

        await self.handle_case_response(ctx, CaseType.UNJAIL, unjail_case.case_id, flags.reason, target)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Unjail(bot))
