import discord
from discord.ext import commands
from loguru import logger

from prisma.enums import CaseType
from tux.bot import Tux
from tux.utils import checks
from tux.utils.flags import JailFlags, generate_usage

from . import ModerationCogBase


class Jail(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.jail.usage = generate_usage(self.jail, JailFlags)

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

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def jail(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        reason: str | None = None,
        *,
        flags: JailFlags,
    ) -> None:
        """
        Jail a member in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to jail.
        reason : str | None
            The reason for the jail.
        flags : JailFlags
            The flags for the command. (silent: bool)

        Raises
        ------
        discord.Forbidden
            If the bot is unable to jail the user.
        discord.HTTPException
            If an error occurs while jailing the user.
        """

        assert ctx.guild

        await ctx.defer(ephemeral=True)

        # Get jail role
        jail_role = await self.get_jail_role(ctx.guild)
        if not jail_role:
            await ctx.send("No jail role found.", ephemeral=True)
            return

        # Check if user is already jailed
        if await self.is_jailed(ctx.guild.id, member.id):
            await ctx.send("User is already jailed.", ephemeral=True)
            return

        # Check if moderator has permission to jail the member
        if not await self.check_conditions(ctx, member, ctx.author, "jail"):
            return

        final_reason = reason or self.DEFAULT_REASON

        # Get roles that can be managed by the bot
        user_roles = self._get_manageable_roles(member, jail_role)

        # Convert roles to IDs
        case_user_roles = [role.id for role in user_roles]

        # Insert case into database
        try:
            case = await self.db.case.insert_case(
                guild_id=ctx.guild.id,
                case_user_id=member.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.JAIL,
                case_reason=final_reason,
                case_user_roles=case_user_roles,
            )

            # Remove roles from member
            if user_roles:
                await member.remove_roles(*user_roles, reason=final_reason, atomic=False)

        except Exception as e:
            logger.error(f"Failed to jail {member}. {e}")
            await ctx.send(f"Failed to jail {member}. {e}", ephemeral=True)
            return

        # Add jail role to member
        try:
            await member.add_roles(jail_role, reason=final_reason)

        except (discord.Forbidden, discord.HTTPException) as e:
            logger.error(f"Failed to jail {member}. {e}")
            await ctx.send(f"Failed to jail {member}. {e}", ephemeral=True)
            return

        # Send DM to member
        dm_sent = await self.send_dm(ctx, flags.silent, member, final_reason, "jailed")

        # Handle case response
        await self.handle_case_response(ctx, CaseType.JAIL, case.case_number, final_reason, member, dm_sent)

    @staticmethod
    def _get_manageable_roles(
        member: discord.Member,
        jail_role: discord.Role,
    ) -> list[discord.Role]:
        """
        Get the roles that can be managed by the bot.

        Parameters
        ----------
        member : discord.Member
            The member to jail.
        jail_role : discord.Role
            The jail role.

        Returns
        -------
        list[discord.Role]
            A list of roles that can be managed by the bot.
        """

        return [
            role
            for role in member.roles
            if not (
                role.is_bot_managed()
                or role.is_premium_subscriber()
                or role.is_integration()
                or role.is_default()
                or role == jail_role
            )
            and role.is_assignable()
        ]


async def setup(bot: Tux) -> None:
    await bot.add_cog(Jail(bot))
