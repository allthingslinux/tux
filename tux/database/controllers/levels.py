import datetime
import math
import time
from pathlib import Path

import discord
import yaml
from loguru import logger

from prisma.models import Guild
from tux.database.client import db


class LevelsController:
    def __init__(self) -> None:
        self.guild = db.guild

        # TODO: Move this to global constants file

        settings_path = Path("config/settings.yml")
        with settings_path.open() as file:
            settings = yaml.safe_load(file)

        self.xp_cooldown = settings.get("XP_COOLDOWN")
        self.levels_exponent = settings.get("LEVELS_EXPONENT")
        self.xp_roles = {role["level"]: role["role_id"] for role in settings["XP_ROLES"]}
        self.xp_multipliers = {role["role_id"]: role["multiplier"] for role in settings["XP_MULTIPLIERS"]}

    """
    READ
    """

    async def ensure_guild_exists(self, guild_id: int) -> Guild:
        """
        Ensure that a guild exists in the database.

        Parameters
        ----------
        guild_id : int
            The ID of the guild.

        Returns
        -------
        Guild
            The guild object.
        """
        guild = await self.guild.find_first(where={"guild_id": guild_id})

        if guild is None:
            return await self.guild.create(data={"guild_id": guild_id})

        return guild

    async def get_xp(self, member_id: int, guild_id: int) -> float:
        # sourcery skip: assign-if-exp, reintroduce-else
        """
        Get the XP for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        xp.xp : float
            The XP of the member.
        """
        await self.ensure_guild_exists(guild_id)

        try:
            xp = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})

            if xp is None:
                return 0
            return xp.xp  # noqa: TRY300

        except Exception as e:
            logger.error(f"Error querying XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0

    async def get_level(self, member_id: int, guild_id: int) -> int:
        # sourcery skip: assign-if-exp, reintroduce-else
        """
        Get the level for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        level.level : int
            The level of the member.
        """
        await self.ensure_guild_exists(guild_id)

        try:
            level = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})

            if level is None:
                return 0
            return level.level  # noqa: TRY300

        except Exception as e:
            logger.error(f"Error querying level for member_id: {member_id}, guild_id: {guild_id}: {e}")
            return 0

    async def is_on_cooldown(self, member_id: int, guild_id: int) -> bool:
        """
        Check if the member is on cooldown.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        bool
            Is the member on cooldown?
        """
        await self.ensure_guild_exists(guild_id)

        last_message_time = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})
        if last_message_time is None:
            return False

        last_message_naive = last_message_time.last_message.replace(tzinfo=None)
        last_message_aware = last_message_naive.replace(tzinfo=datetime.UTC)
        time_between_messages = datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC) - last_message_aware

        cooldown_period = datetime.timedelta(seconds=self.xp_cooldown)

        return time_between_messages < cooldown_period

    async def is_blacklisted(self, member_id: int, guild_id: int) -> bool:
        """
        Get the level for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        bool
            Is the member blacklisted?
        """
        await self.ensure_guild_exists(guild_id)

        blacklisted = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})

        return False if blacklisted is None else blacklisted.blacklisted

    """
    UPDATE
    """

    async def increment_xp(self, member_id: int, guild_id: int, member: discord.Member, guild: discord.Guild) -> None:
        """
        Increment the XP for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        member : discord.Member
            The member to assign the role to.
        guild : discord.Guild
            The guild where the member is located.
        """
        await self.ensure_guild_exists(guild.id)

        try:
            xp = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})

            if xp is None:
                await db.levels.create(
                    data={
                        "member_id": member_id,
                        "guild_id": guild_id,
                        "xp": 0,
                        "last_message": datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC),
                    },
                )

            if await self.is_on_cooldown(member_id, guild_id):
                await db.levels.update(
                    where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                    data={"last_message": datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC)},
                )
                return

            if await self.is_blacklisted(member_id, guild_id):
                return

            multiplier = 1
            for role in member.roles:
                multiplier = max(multiplier, self.xp_multipliers[role.id]) if role.id in self.xp_multipliers else 1

            xp_increment = 1 * multiplier

            await db.levels.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={
                    "xp": {"increment": xp_increment},
                    "last_message": datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC),
                },
            )

            await self.calculate_level(member_id, guild_id, member, guild)

        except Exception as e:
            logger.error(f"Error incrementing XP for member_id: {member_id}, guild_id: {guild_id}: {e}")

    async def set_xp(
        self,
        member_id: int,
        guild_id: int,
        xp_amount: int,
        member: discord.Member,
        guild: discord.Guild,
    ) -> None:
        """
        Set the XP for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        xp_amount : int
            The amount of XP to set the member to.
        member : discord.Member
            The member to assign the role to.
        guild : discord.Guild
            The guild where the member is located.
        """
        await self.ensure_guild_exists(guild.id)

        try:
            await db.levels.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"xp": xp_amount},
            )

        except Exception as e:
            logger.error(f"Error setting XP for member_id: {member_id}, guild_id: {guild_id}: {e}")

        await self.calculate_level(member_id, guild_id, member, guild)

    async def set_level(
        self,
        member_id: int,
        guild_id: int,
        new_level: int,
        member: discord.Member,
        guild: discord.Guild,
    ) -> None:
        """
        Set the level for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        new_level : int
            The level to set the member to.
        member : discord.Member
            The member to assign the role to.
        guild : discord.Guild
            The guild where the member is located.
        """
        await self.ensure_guild_exists(guild.id)

        try:
            xp = math.ceil(500 * (new_level / 5) ** self.levels_exponent)

            await db.levels.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"xp": xp, "level": new_level},
            )

        except Exception as e:
            logger.error(f"Error setting XP for member_id: {member_id}, guild_id: {guild_id}: {e}")

        await self.calculate_level(member_id, guild_id, member, guild)

    async def calculate_level(self, member_id: int, guild_id: int, member: discord.Member, guild: discord.Guild) -> int:
        """
        Calculate the level based on XP.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        member : discord.Member
            The member to assign the role to.
        guild : discord.Guild
            The guild where the member is located.

        Returns
        -------
        int
            The level of the member.
        """
        await self.ensure_guild_exists(guild.id)

        member_xp = await self.get_xp(member_id, guild_id)
        current_member_level = await self.get_level(member_id, guild_id)

        new_member_level = int((member_xp / 500) ** (1 / self.levels_exponent) * 5)

        if new_member_level != current_member_level:
            await db.levels.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"level": new_member_level},
            )

            await self.update_roles(member, guild, new_member_level)

        return new_member_level

    # TODO: update_roles function needs refactoring and moved outside controller
    async def update_roles(self, member: discord.Member, guild: discord.Guild, new_member_level: int) -> None:
        """
        Update the roles for a member based on their level.

        Parameters
        ----------
        member : discord.Member
            The member to assign the role to.
        guild : discord.Guild
            The guild where the member is located.
        new_member_level : int
            The new level of the member to process.
        """

        await self.ensure_guild_exists(guild.id)

        role_id = None

        for lvl, rid in sorted(self.xp_roles.items()):
            if new_member_level >= lvl:
                role_id = rid
            else:
                break

        if role_id:
            if role := guild.get_role(role_id):
                await self.try_assign_role(member, role)

                for other_role_id in self.xp_roles.values():
                    if other_role_id != role_id:
                        other_role = guild.get_role(other_role_id)
                        if other_role in member.roles:
                            await member.remove_roles(other_role)

            else:
                logger.error(f"Role ID {role_id} not found in guild {guild.name}")

        else:
            for other_role_id in self.xp_roles.values():
                other_role = guild.get_role(other_role_id)

                if other_role in member.roles:
                    await member.remove_roles(other_role)

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
            await member.add_roles(role)

        except Exception as error:
            logger.error(f"Failed to assign role {role.name} to {member}: {error}")

    async def toggle_blacklist(self, member_id: int, guild_id: int) -> bool:
        """
        Toggle the blacklist status for a member in a guild.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.

        Returns
        -------
        bool
            Is the member blacklisted?
        """
        await self.ensure_guild_exists(guild_id)

        try:
            blacklisted = await db.levels.find_first(where={"member_id": member_id, "guild_id": guild_id})

            if blacklisted is None:
                await db.levels.create(data={"member_id": member_id, "guild_id": guild_id, "blacklisted": True})

            else:
                await db.levels.update(
                    where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                    data={"blacklisted": not blacklisted.blacklisted},
                )
                return blacklisted.blacklisted

        except Exception as e:
            logger.error(f"Error toggling blacklist for member_id: {member_id}, guild_id: {guild_id}: {e}")

        return False

    async def reset_xp(self, member_id: int, guild_id: int, member: discord.Member, guild: discord.Guild) -> None:
        """
        Reset the XP for a member in a guild and remove all roles.

        Parameters
        ----------
        member_id : int
            The ID of the member.
        guild_id : int
            The ID of the guild.
        member : discord.Member
            The member to remove the roles from.
        guild : discord.Guild
            The guild where the member is located.
        """
        try:
            await db.levels.update(
                where={"member_id_guild_id": {"member_id": member_id, "guild_id": guild_id}},
                data={"xp": 0, "level": 0},
            )

            for role_id in self.xp_roles.values():
                role = guild.get_role(role_id)

                if role and role in member.roles:
                    await member.remove_roles(role)

        except Exception as e:
            logger.error(f"Error resetting XP for member_id: {member_id}, guild_id: {guild_id}: {e}")
