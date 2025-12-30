"""
Detection and warning system for potentially harmful commands.

This plugin monitors Discord messages for dangerous shell commands like
recursive file deletion, fork bombs, and destructive disk operations,
providing warnings to prevent accidental system damage.
"""

import re

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.shared.config.settings import CONFIG
from tux.shared.functions import strip_formatting

# Configuration

DANGEROUS_RM_COMMANDS = (
    # Privilege escalation prefixes
    r"(?:sudo\s+|doas\s+|run0\s+)?"
    # rm command
    r"\brm\b\s+"
    # rm options
    r"(?:-[frR]+|--force|--recursive|--no-preserve-root|\s+)*"
    # Root/home indicators
    r"(?:[/\∕~]\s*|\.(?:/|\.)\s*|\*|"  # noqa: RUF001
    # Critical system paths
    r"/(?:bin|boot|etc|lib|proc|root|sys|tmp|usr|var(?:/log)?|network\.|system))"
    # Additional dangerous flags
    r"(?:\s+--no-preserve-root|\s+\*)*"
)

FORK_BOMB_PATTERNS = [":(){:&};:", ":(){:|:&};:"]

DANGEROUS_DD_COMMANDS = r"dd\s+.*of=/dev/([hs]d[a-z]|nvme\d+n\d+)"

FORMAT_COMMANDS = r"mkfs\..*\s+/dev/([hs]d[a-z]|nvme\d+n\d+)"

# -- DO NOT CHANGE ANYTHING BELOW THIS LINE --


class HarmfulCommands(BaseCog):
    """Discord cog for detecting and warning about harmful shell commands."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the harmful commands detector.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        self.bot = bot

    def is_harmful(self, command: str) -> str | None:
        # sourcery skip: assign-if-exp, boolean-if-exp-identity, reintroduce-else
        """
        Check if a command is potentially harmful to the system.

        Parameters
        ----------
        command : str
            The command to check.

        Returns
        -------
        bool
            True if the command is harmful, False otherwise.
        """
        # Normalize command by removing all whitespace for fork bomb check
        normalized = "".join(command.strip().lower().split())
        if normalized in FORK_BOMB_PATTERNS:
            return "FORK_BOMB"

        # Check for dangerous rm commands
        if re.search(DANGEROUS_RM_COMMANDS, command, re.IGNORECASE):
            return "RM_COMMAND"

        # Check for dangerous dd commands
        if re.search(DANGEROUS_DD_COMMANDS, command, re.IGNORECASE):
            return "DD_COMMAND"

        # Check for format commands
        if bool(re.search(FORMAT_COMMANDS, command, re.IGNORECASE)):
            return "FORMAT_COMMAND"
        return None

    async def handle_harmful_message(self, message: discord.Message) -> None:
        """
        Detect harmful linux commands and replies to the user with a warning if they are detected.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        if (
            message.author.bot
            and message.webhook_id not in CONFIG.IRC_CONFIG.BRIDGE_WEBHOOK_IDS
        ):
            return

        stripped_content = strip_formatting(message.content)
        harmful = self.is_harmful(stripped_content)

        if harmful == "RM_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, all directory contents will be deleted. There is no undo. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "FORK_BOMB":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, all the memory in your system will be used. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "DD_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, your disk will be overwritten or erased irreversibly. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )
            return
        if harmful == "FORMAT_COMMAND":
            await message.reply(
                "-# ⚠️ **This command is likely harmful. By running it, your disk will be formatted. Ensure you fully understand the consequences before proceeding. If you have received this message in error, please disregard it.**",
            )

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message,
    ) -> None:
        """Handle message edits to check for newly harmful content."""
        if not self.is_harmful(before.content) and self.is_harmful(after.content):
            await self.handle_harmful_message(after)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Handle new messages to check for harmful content."""
        await self.handle_harmful_message(message)


async def setup(bot: Tux) -> None:
    """Cog setup for harmful command plugin.

    Parameters
    ----------
    bot : Tux
        The bot instance.
    """
    await bot.add_cog(HarmfulCommands(bot))
