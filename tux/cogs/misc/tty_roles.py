import datetime
import math

import discord
from discord.ext import commands
from loguru import logger


class TtyRoles(commands.Cog):
    """
    A cog that assigns roles to users based on the number of users in the guild.

    Attributes
    ----------
    bot : commands.Bot
        The bot instance.
    base_role_name : str
        The base name for the roles.
    """

    def __init__(self, bot: commands.Bot):
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

        role = self.get_role_by_name(member, role_name) or await self.try_create_role(member, role_name)

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

        exponent = int(math.floor(math.log2(user_count)))

        return f"{self.base_role_name}{2 ** exponent}"

    @staticmethod
    def get_role_by_name(member: discord.Member, role_name: str) -> discord.Role | None:
        """
        Get a role by name from the guild.

        Parameters
        ----------
        member : discord.Member
            The member whose guild to search for the role.
        role_name : str
            The name of the role to search for.

        Returns
        -------
        discord.Role | None
            The role if found, otherwise None.
        """

        return discord.utils.get(member.guild.roles, name=role_name)

    @staticmethod
    async def try_create_role(member: discord.Member, role_name: str) -> discord.Role | None:
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
            await discord.utils.sleep_until(datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=5))
            await member.add_roles(role)

        except Exception as error:
            logger.error(f"Failed to assign role {role.name} to {member}: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TtyRoles(bot))
