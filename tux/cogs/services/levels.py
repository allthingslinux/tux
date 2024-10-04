import datetime
import time
from pathlib import Path

import discord
import yaml
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.database.controllers.levels import LevelsController
from tux.main import get_prefix
from tux.ui.embeds import EmbedCreator

settings_path = Path("config/settings.yml")
with settings_path.open() as file:
    settings = yaml.safe_load(file)


class LevelsService(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_controller = LevelsController()
        self.xp_cooldown = settings.get("XP_COOLDOWN")
        self.levels_exponent = settings.get("LEVELS_EXPONENT")
        self.xp_roles = {role["level"]: role["role_id"] for role in settings["XP_ROLES"]}
        self.xp_multipliers = {role["role_id"]: role["multiplier"] for role in settings["XP_MULTIPLIERS"]}

    @commands.Cog.listener("on_message")
    async def xp_listener(self, message: discord.Message) -> None:
        """
        Listens for messages to process XP gain.

        Parameters
        ----------
        message : discord.Message
            The message object.
        """
        if message.author.bot or message.guild is None or message.channel.id in settings["XP_BLACKLIST_CHANNEL"]:
            return

        prefixes = await get_prefix(self.bot, message)
        if any(message.content.startswith(prefix) for prefix in prefixes):
            return

        member = message.guild.get_member(message.author.id)
        if member is None:
            return

        await self.process_xp_gain(member, message.guild)

    async def process_xp_gain(self, member: discord.Member, guild: discord.Guild) -> None:
        """
        Processes XP gain for a member.

        Parameters
        ----------
        member : discord.Member
            The member gaining XP.
        guild : discord.Guild
            The guild where the member is gaining XP.
        """
        if await self.levels_controller.is_blacklisted(member.id, guild.id):
            return

        last_message_time = await self.levels_controller.get_last_message_time(member.id, guild.id)
        if last_message_time and self.is_on_cooldown(last_message_time):
            return

        current_xp, current_level = await self.levels_controller.get_xp_and_level(member.id, guild.id)

        xp_increment = self.calculate_xp_increment(member)
        new_xp = current_xp + xp_increment
        new_level = self.calculate_level(new_xp)

        await self.levels_controller.update_xp_and_level(
            member.id,
            guild.id,
            new_xp,
            new_level,
            datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC),
        )

        if new_level > current_level:
            logger.debug(f"User {member.name} leveled up from {current_level} to {new_level} in guild {guild.name}")
            await self.handle_level_up(member, guild, new_level)

    def is_on_cooldown(self, last_message_time: datetime.datetime) -> bool:
        """
        Checks if the member is on cooldown.

        Parameters
        ----------
        last_message_time : datetime.datetime
            The time of the last message.

        Returns
        -------
        bool
            True if the member is on cooldown, False otherwise.
        """
        return (datetime.datetime.fromtimestamp(time.time(), tz=datetime.UTC) - last_message_time) < datetime.timedelta(
            seconds=self.xp_cooldown,
        )

    def calculate_xp_increment(self, member: discord.Member) -> float:
        """
        Calculates the XP increment for a member.

        Parameters
        ----------
        member : discord.Member
            The member gaining XP.

        Returns
        -------
        float
            The XP increment.
        """
        return max((self.xp_multipliers.get(role.id, 1) for role in member.roles), default=1)

    def calculate_level(self, xp: float) -> int:
        """
        Calculates the level based on XP.

        Parameters
        ----------
        xp : float
            The XP amount.

        Returns
        -------
        int
            The calculated level.
        """
        return int((xp / 500) ** (1 / self.levels_exponent) * 5)

    async def handle_level_up(self, member: discord.Member, guild: discord.Guild, new_level: int) -> None:
        """
        Handles the level up process for a member.

        Parameters
        ----------
        member : discord.Member
            The member leveling up.
        guild : discord.Guild
            The guild where the member is leveling up.
        new_level : int
            The new level of the member.
        """
        await self.update_roles(member, guild, new_level)
        # we can add more to this like level announcements etc. That's why I keep this function in between.

    async def update_roles(self, member: discord.Member, guild: discord.Guild, new_level: int) -> None:
        """
        Updates the roles of a member based on their new level.

        Parameters
        ----------
        member : discord.Member
            The member whose roles are being updated.
        guild : discord.Guild
            The guild where the member's roles are being updated.
        new_level : int
            The new level of the member.
        """
        roles_to_assign = [guild.get_role(rid) for lvl, rid in sorted(self.xp_roles.items()) if new_level >= lvl]
        highest_role = roles_to_assign[-1] if roles_to_assign else None

        if highest_role:
            await self.try_assign_role(member, highest_role)

        roles_to_remove = [r for r in member.roles if r.id in self.xp_roles.values() and r != highest_role]
        await member.remove_roles(*roles_to_remove)
        logger.debug(
            f"Assigned role {highest_role.name if highest_role else 'None'} to member {member} and removed roles {', '.join(r.name for r in roles_to_remove)}",
        )

    @staticmethod
    async def try_assign_role(member: discord.Member, role: discord.Role) -> None:
        """
        Tries to assign a role to a member.

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

    def calculate_xp_for_level(self, level: int) -> float:
        """
        Calculates the XP required for a given level.

        Parameters
        ----------
        level : int
            The level to calculate XP for.

        Returns
        -------
        float
            The XP required for the level.
        """
        return 500 * (level / 5) ** self.levels_exponent

    def valid_xplevel_input(self, user_input: int) -> discord.Embed | None:
        """
        Check if the input is valid.

        Do not move this function to utils.py, as this results in a circular import.

        Parameters
        ----------
        user_input : int
            The input to check.

        Returns
        -------
        discord.Embed | None
            A string if the input is valid, or a discord. Embed if there is an error.
        """
        if user_input >= 2**63 - 1:
            embed: discord.Embed = EmbedCreator.create_embed(
                embed_type=EmbedCreator.ERROR,
                title="Error",
                description="Input must be less than the integer limit (2^63).",
            )
            return embed

        if user_input < 0:
            embed: discord.Embed = EmbedCreator.create_embed(
                embed_type=EmbedCreator.ERROR,
                title="Error",
                description="Input must be a positive integer.",
            )
            return embed

        return None


async def setup(bot: Tux) -> None:
    await bot.add_cog(LevelsService(bot))
