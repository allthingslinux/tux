import re

import discord
from discord.ext import commands

harmful_command_pattern = r"(?:sudo\s+|doas\s+|run0\s+)?rm\s+(-[frR]*|--force|--recursive|--no-preserve-root|\s+)*(/\s*|\*|/bin|/boot|/etc|/lib|/proc|/root|/sbin|/sys|/tmp|/usr|/var|/var/log|/network.|/system)(\s+--no-preserve-root|\s+\*)*|:\(\)\{ :|:& \};:"


def is_harmful(command: str) -> bool:
    first_test: bool = re.search(harmful_command_pattern, command) is not None
    second_test: bool = re.search(r"rm.{0,5}[rfRF]", command) is not None

    return first_test and second_test


class AutoRespond(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def strip_formatting(self, content: str) -> str:
        # Remove triple backtick blocks considering any spaces and platform-specific newlines
        content = re.sub(r"`/```(.*)```/", "", content, flags=re.DOTALL)

        # Remove inline code snippets preserving their content only
        content = re.sub(r"`([^`]*)`", r"\1", content)

        # Remove Markdown headers
        content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)

        # Remove other common markdown symbols
        content = re.sub(r"[\*_~|>]", "", content)

        return content.strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        When a message is sent in a guild

        Parameters
        ----------
        message : discord.Message
            The message that was sent.
        """

        if message.author.bot:
            return

        # Strip the message content of any formatting
        stripped_content = self.strip_formatting(message.content)

        # Check if the stripped content is in the list of harmful commands
        if is_harmful(stripped_content):
            await message.reply(
                "Warning: This command is potentially harmful. Please avoid running it unless you are fully aware of its operation. If this was a mistake, please disregard this message."
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoRespond(bot))
