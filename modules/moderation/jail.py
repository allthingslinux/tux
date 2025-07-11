import discord
from bot import Tux
from discord.ext import commands
from loguru import logger
from utils import checks
from utils.flags import JailFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

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
        jail_role_id = await self.db.guild_config.get_jail_role_id(guild.id)
        return None if jail_role_id is None else guild.get_role(jail_role_id)

    async def get_jail_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """
        Get the jail channel for the guild.
        """
        jail_channel_id = await self.db.guild_config.get_jail_channel_id(guild.id)
        channel = guild.get_channel(jail_channel_id) if jail_channel_id is not None else None
        return channel if isinstance(channel, discord.TextChannel) else None

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
        # Get latest case for this user (more efficient than counting all cases)
        latest_case = await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            case_types=[CaseType.JAIL, CaseType.UNJAIL],
        )

        # If no cases exist or latest case is an unjail, user is not jailed
        return bool(latest_case and latest_case.case_type == CaseType.JAIL)

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
        flags : JailFlags
            The flags for the command. (reason: str, silent: bool)

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

        # Get jail channel
        jail_channel = await self.get_jail_channel(ctx.guild)
        if not jail_channel:
            await ctx.send("No jail channel found.", ephemeral=True)
            return

        # Check if user is already jailed
        if await self.is_jailed(ctx.guild.id, member.id):
            await ctx.send("User is already jailed.", ephemeral=True)
            return

        # Check if moderator has permission to jail the member
        if not await self.check_conditions(ctx, member, ctx.author, "jail"):
            return

        # Use a transaction-like pattern to ensure consistency
        try:
            # Get roles that can be managed by the bot
            user_roles = self._get_manageable_roles(member, jail_role)

            # Convert roles to IDs
            case_user_roles = [role.id for role in user_roles]

            # First create the case - if this fails, no role changes are made
            case = await self.db.case.insert_case(
                guild_id=ctx.guild.id,
                case_user_id=member.id,
                case_moderator_id=ctx.author.id,
                case_type=CaseType.JAIL,
                case_reason=flags.reason,
                case_user_roles=case_user_roles,
            )

            # Add jail role immediately - this is the most important part
            await member.add_roles(jail_role, reason=flags.reason)

            # Send DM to member
            dm_sent = await self.send_dm(ctx, flags.silent, member, flags.reason, "jailed")

            # Handle case response - send embed immediately
            await self.handle_case_response(ctx, CaseType.JAIL, case.case_number, flags.reason, member, dm_sent)

            # Remove old roles in the background after sending the response
            if user_roles:
                try:
                    # Try to remove all at once for efficiency
                    await member.remove_roles(*user_roles, reason=flags.reason)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove all roles at once from {member}, falling back to individual removal: {e}",
                    )
                    # Fall back to removing one by one
                    for role in user_roles:
                        try:
                            await member.remove_roles(role, reason=flags.reason)
                        except Exception as role_e:
                            logger.error(f"Failed to remove role {role} from {member}: {role_e}")
                            # Continue with other roles even if one fails

        except Exception as e:
            logger.error(f"Failed to jail {member}: {e}")
            await ctx.send(f"Failed to jail {member}: {e}", ephemeral=True)
            return

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
