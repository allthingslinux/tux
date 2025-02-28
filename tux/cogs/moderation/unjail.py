import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from prisma.models import Case
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import UnjailFlags, generate_usage

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.unjail.usage = generate_usage(self.unjail, UnjailFlags)

    async def get_jail_role(self, guild: discord.Guild) -> discord.Role | None:
        """
        Get the jail role for the guild.

        Parameters
        ----------
        guild : discord.Guild
            The guild to get the jail role for.

        Returns
        -------
        discord.Role | None
            The jail role, or None if not found.
        """
        jail_role_id = await self.config.get_jail_role_id(guild.id)
        return None if jail_role_id is None else guild.get_role(jail_role_id)

    async def is_jailed(self, guild_id: int, user_id: int) -> bool:
        """
        Check if a user is jailed.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        bool
            True if the user is jailed, False otherwise.
        """
        jail_cases = await self.db.case.get_all_cases_by_type(guild_id, CaseType.JAIL)
        unjail_cases = await self.db.case.get_all_cases_by_type(guild_id, CaseType.UNJAIL)

        jail_count = sum(case.case_user_id == user_id for case in jail_cases)
        unjail_count = sum(case.case_user_id == user_id for case in unjail_cases)

        return jail_count > unjail_count

    async def get_latest_jail_case(self, guild_id: int, user_id: int) -> Case | None:
        """
        Get the latest jail case for a user.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        Case | None
            The latest jail case, or None if not found.
        """
        cases = await self.db.case.get_all_cases_by_type(guild_id, CaseType.JAIL)
        user_cases = [case for case in cases if case.case_user_id == user_id]
        return user_cases[-1] if user_cases else None

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
        reason: str | None = None,
        *,
        flags: UnjailFlags,
    ) -> None:
        """
        Remove a member from jail.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to unjail.
        reason : str | None
            The reason for removing from jail.
        flags : UnjailFlags
            The flags for the command. (silent: bool)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to unjail the user.
        discord.HTTPException
            If an error occurs while unjailing the user.
        """

        assert ctx.guild

        await ctx.defer(ephemeral=True)

        # Get jail role
        jail_role = await self.get_jail_role(ctx.guild)
        if not jail_role:
            await ctx.send("No jail role found.", ephemeral=True)
            return

        # Check if user is jailed
        if not await self.is_jailed(ctx.guild.id, member.id):
            await ctx.send("User is not jailed.", ephemeral=True)
            return

        # Check if moderator has permission to unjail the member
        if not await self.check_conditions(ctx, member, ctx.author, "unjail"):
            return

        final_reason = reason or self.DEFAULT_REASON

        try:
            # Get latest jail case
            case = await self.get_latest_jail_case(ctx.guild.id, member.id)
            if not case:
                await ctx.send("No jail case found.", ephemeral=True)
                return

            # Remove jail role from member
            await member.remove_roles(jail_role, reason=final_reason)

            # Add roles back to member
            if case.case_user_roles:
                roles = [role for role_id in case.case_user_roles if (role := ctx.guild.get_role(role_id)) is not None]
                if roles:
                    await member.add_roles(*roles, reason=final_reason, atomic=False)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to unjail {member}. {e}")
            await ctx.send(f"Failed to unjail {member}. {e}", ephemeral=True)
            return

        # Insert unjail case into database
        case = await self.db.case.insert_case(
            case_user_id=member.id,
            case_moderator_id=ctx.author.id,
            case_type=CaseType.UNJAIL,
            case_reason=final_reason,
            guild_id=ctx.guild.id,
        )

        # Send DM to member
        dm_sent = await self.send_dm(ctx, flags.silent, member, final_reason, "removed from jail")

        # Handle case response
        await self.handle_case_response(
            ctx,
            CaseType.UNJAIL,
            case.case_number,
            final_reason,
            member,
            dm_sent,
        )


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unjail(bot))
