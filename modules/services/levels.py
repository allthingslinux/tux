import datetime
import time

import discord
from app import get_prefix
from bot import Tux
from database.controllers import DatabaseController
from discord.ext import commands
from loguru import logger
from ui.embeds import EmbedCreator
from utils.config import CONFIG


class LevelsService(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController()
        self.xp_cooldown = CONFIG.XP_COOLDOWN
        self.levels_exponent = CONFIG.LEVELS_EXPONENT
        self.xp_roles = {role["level"]: role["role_id"] for role in CONFIG.XP_ROLES}
        self.xp_multipliers = {role["role_id"]: role["multiplier"] for role in CONFIG.XP_MULTIPLIERS}
        self.max_level = max(item["level"] for item in CONFIG.XP_ROLES)
        self.enable_xp_cap = CONFIG.ENABLE_XP_CAP

    @commands.Cog.listener("on_message")
    async def xp_listener(self, message: discord.Message) -> None:
        """
        Listens for messages to process XP gain.

        Parameters
        ----------
        message : discord.Message
            The message object.
        """
        if message.author.bot or message.guild is None or message.channel.id in CONFIG.XP_BLACKLIST_CHANNELS:
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
        # Get blacklist status
        is_blacklisted = await self.db.levels.is_blacklisted(member.id, guild.id)
        if is_blacklisted:
            return

        last_message_time = await self.db.levels.get_last_message_time(member.id, guild.id)
        if last_message_time and self.is_on_cooldown(last_message_time):
            return

        current_xp, current_level = await self.db.levels.get_xp_and_level(member.id, guild.id)

        xp_increment = self.calculate_xp_increment(member)
        new_xp = current_xp + xp_increment
        new_level = self.calculate_level(new_xp)

        await self.db.levels.update_xp_and_level(
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

        if highest_role or roles_to_remove:
            logger.debug(
                f"Updated roles for {member}: {f'Assigned {highest_role.name}' if highest_role else 'No role assigned'}{', Removed: ' + ', '.join(r.name for r in roles_to_remove) if roles_to_remove else ''}",
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

    # *NOTE* Do not move this function to utils.py, as this results in a circular import.
    def valid_xplevel_input(self, user_input: int) -> discord.Embed | None:
        """
        Check if the input is valid.

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

    @staticmethod
    def generate_progress_bar(
        current_value: int,
        target_value: int,
        bar_length: int = 10,
    ) -> str:
        """
        Generates an XP progress bar based on the current level and XP.

        Parameters
        ----------
        current_value : int
            The current XP value.
        target_value : int
            The target XP value.
        bar_length : int, optional
            The length of the progress bar. Defaults to 10.

        Returns
        -------
        str
            The formatted progress bar.
        """
        progress: float = current_value / target_value

        filled_length: int = int(bar_length * progress)
        empty_length: int = bar_length - filled_length

        bar: str = "▰" * filled_length + "▱" * empty_length

        return f"`{bar}` {current_value}/{target_value}"

    def get_level_progress(self, xp: float, level: int) -> tuple[int, int]:
        """
        Get the progress towards the next level.

        Parameters
        ----------
        xp : float
            The current XP.
        level : int
            The current level.

        Returns
        -------
        tuple[int, int]
            A tuple containing the XP progress within the current level and the XP required for the next level.
        """
        current_level_xp = self.calculate_xp_for_level(level)
        next_level_xp = self.calculate_xp_for_level(level + 1)

        xp_progress = int(xp - current_level_xp)
        xp_required = int(next_level_xp - current_level_xp)

        return xp_progress, xp_required


async def setup(bot: Tux) -> None:
    await bot.add_cog(LevelsService(bot))
