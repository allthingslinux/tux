import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.utils import checks
from tux.utils.flags import JailFlags

from . import ModerationCogBase


class Jail(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
        usage="jail [target] [reason] <silent>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def jail(  # noqa: PLR0911
        self,
        ctx: commands.Context[commands.Bot],
        target: discord.Member,
        *,
        flags: JailFlags,
    ) -> None:
        """
        Jail a user in the server.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The discord context object.
        target : discord.Member
            The member to jail.
        flags : JailFlags
            The flags for the command. (reason: str, silent: bool)
        """

        if not ctx.guild:
            logger.warning("Jail command used outside of a guild context.")
            return

        moderator = ctx.author

        if not await self.check_conditions(ctx, target, moderator, "jail"):
            return

        jail_role_id = await self.config.get_jail_role_id(ctx.guild.id)
        if not jail_role_id:
            await ctx.send("No jail role has been set up for this server.", delete_after=30, ephemeral=True)
            return

        jail_role = ctx.guild.get_role(jail_role_id)
        if not jail_role:
            await ctx.send("The jail role has been deleted.", delete_after=30, ephemeral=True)
            return

        target_roles: list[discord.Role] = self._get_manageable_roles(target, jail_role)
        if jail_role in target.roles:
            await ctx.send("The user is already jailed.", delete_after=30, ephemeral=True)
            return

        case_target_roles = [role.id for role in target_roles]

        try:
            case = await self.db.case.insert_case(
                case_target_id=target.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.JAIL,
                case_reason=flags.reason,
                guild_id=ctx.guild.id,
                case_target_roles=case_target_roles,
            )

        except Exception as e:
            logger.error(f"Failed to jail {target}. {e}")
            await ctx.send(f"Failed to jail {target}. {e}", delete_after=30, ephemeral=True)
            return

        try:
            if target_roles:
                await target.remove_roles(*target_roles, reason=flags.reason, atomic=False)
                await target.add_roles(jail_role, reason=flags.reason)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to jail {target}. {e}")
            await ctx.send(f"Failed to jail {target}. {e}", delete_after=30, ephemeral=True)
            return

        await self.send_dm(ctx, flags.silent, target, flags.reason, "jailed")
        await self.handle_case_response(ctx, CaseType.JAIL, case.case_id, flags.reason, target)

    def _get_manageable_roles(
        self,
        target: discord.Member,
        jail_role: discord.Role,
    ) -> list[discord.Role]:
        """
        Get the roles that can be managed by the bot.

        Parameters
        ----------
        target : discord.Member
            The member to jail.
        jail_role : discord.Role
            The jail role.

        Returns
        -------
        list[discord.Role]
            The roles that can be managed by the bot.
        """

        return [
            role
            for role in target.roles
            if not (
                role.is_bot_managed()
                or role.is_premium_subscriber()
                or role.is_integration()
                or role.is_default()
                or role == jail_role
            )
            and role.is_assignable()
        ]


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Jail(bot))
