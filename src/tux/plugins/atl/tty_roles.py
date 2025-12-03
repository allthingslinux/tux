"""
TTY Roles Plugin for Tux Bot.

This plugin automatically assigns roles to users based on the guild member count,
using a naming scheme based on TTY device names (/dev/ttyN).
"""

import datetime
import math

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux


class TtyRoles(BaseCog):
    """Plugin for automatically assigning TTY-based roles based on member count."""

    def __init__(self, bot: Tux):
        """Initialize the TtyRoles plugin.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the plugin with.
        """
        self.bot = bot
        self.base_role_name = "/dev/tty"

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """
        Assign a role to a user based on the number of users in the guild.

        Parameters
        ----------
        member : discord.Member
            The member that joined the guild.
        """
        user_count = member.guild.member_count
        role_name = self._compute_role_name(user_count)

        role = discord.utils.get(
            member.guild.roles,
            name=role_name,
        ) or await self.try_create_role(member, role_name)

        if role:
            await self.try_assign_role(member, role)

    def _compute_role_name(self, user_count: int | None) -> str:
        """
        Compute the role name based on the number of users in the guild.

        Parameters
        ----------
        user_count : int | None
            The number of users in the guild.

        Returns
        -------
        str
            The name of the role to assign to the user.
        """
        if user_count is None:
            return ""

        if 1 <= user_count <= 128:
            return f"{self.base_role_name}0"

        exponent = math.floor(math.log2(user_count))

        return f"{self.base_role_name}{2**exponent}"

    @staticmethod
    async def try_create_role(
        member: discord.Member,
        role_name: str,
    ) -> discord.Role | None:
        """
        Create a role in the guild.

        Parameters
        ----------
        member : discord.Member
            The member whose guild to create the role in.
        role_name : str
            The name of the role to create.

        Returns
        -------
        discord.Role | None
            The created role if successful, otherwise None.
        """
        try:
            return await member.guild.create_role(name=role_name)

        except Exception as error:
            logger.error(f"Failed to create role {role_name}: {error}")

        return None

    @staticmethod
    async def try_assign_role(member: discord.Member, role: discord.Role) -> None:
        """
        Assign a role to a member.

        Parameters
        ----------
        member : discord.Member
            The member to assign the role to.
        role : discord.Role
            The role to assign.
        """
        try:
            await discord.utils.sleep_until(
                datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=5),
            )
            await member.add_roles(role)

        except discord.NotFound as error:
            # check if the member left the server
            if member.guild.get_member(member.id) is None:
                logger.info(
                    f"Member {member} left or got kicked by the server before the role could be assigned.",
                )
                return
            logger.error(f"Failed to assign role {role.name} to {member}: {error}")

        except Exception as error:
            logger.error(f"Failed to assign role {role.name} to {member}: {error}")


async def setup(bot: Tux) -> None:
    """Set up the tty_roles plugin.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(TtyRoles(bot))
