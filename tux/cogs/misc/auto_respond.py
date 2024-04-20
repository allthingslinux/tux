import re

import discord
from discord.ext import commands

harmful_commands = [
    "doas rm -fr /*",
    "doas rm -rf /*",
    "doas rm -rf /",
    "doas rm -rf / --no-preserve-root",
    "doas rm -rf /* --no-preserve-root",
    "rm --force / --recursive",
    "rm --force /* --recursive",
    "rm --recursive --force /",
    "rm --recursive --force /*",
    "rm --recursive / --force",
    "rm --recursive /* --force",
    "rm --recursive /network.",
    "rm --recursive /system",
    "rm -f --recursive /",
    "rm -f --recursive /*",
    "rm -fR /",
    "rm -fR /*",
    "rm -r -f /",
    "rm -r -f /*",
    "rm -R -f /*",
    "rm -R -f /",
    "rm -rf /",
    "rm -rf /*",
    "rm -Rf /*",
    "rm -Rf /",
    "rm rf /*",
    "sudo rm --force --recursive /",
    "sudo rm --force --recursive /*",
    "sudo rm --force --recursive / --no-preserve-root",
    "sudo rm --force --recursive /* --no-preserve-root",
    "sudo rm -fR /",
    "sudo rm -fR /*",
    "sudo rm -r -f / --no-preserve-root",
    "sudo rm -r -f /* --no-preserve-root",
    "sudo rm -rf --no-preserve-root",
    "sudo rm -rf --no-preserve-root /",
    "sudo rm -rf /*",
    "sudo rm -rf /",
    "sudo rm -rf /* --no-preserve-root",
    "sudo rm -rf / --no-preserve-root",
    "sudo rm -rf /* --no-preserve-root *",
    "sudo rm -rf /bin",
    "sudo rm -rf /boot",
    "sudo rm -rf /etc",
    "sudo rm -rf /lib",
    "sudo rm -rf /proc",
    "sudo rm -rf /root",
    "sudo rm -rf /sbin",
    "sudo rm -rf /sys",
    "sudo rm -rf /tmp /*",
    "sudo rm -rf /usr",
    "sudo rm -rf /var",
    "sudo rm -rf /var/log",
    "sudo rm -fr /",
    "sudo rm -fr /*",
    "sudo rm -rf /*",
    "sudo su -c 'rm -rf /'",
    ":(){ :|: & };:",
    "sudo rm -rf /",
]

# TODO: Fix the triple backtick  regex as it is not working


class AutoRespond(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def strip_formatting(self, content: str) -> str:
        # Remove triple backtick blocks considering any spaces and platform-specific newlines
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

        # Remove inline code snippets preserving their content only
        content = re.sub(r"`([^`]*)`", r"\1", content)

        # Remove Markdown headers
        content = re.sub(r"^#+\s+", "", content, flags=re.MULTILINE)

        # Remove other common markdown symbols
        content = re.sub(r"[\*_~|>]", "", content)

        return content.strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        stripped_content = self.strip_formatting(message.content)

        if stripped_content in harmful_commands:
            await message.reply(
                "Warning: This command is potentially harmful. Please avoid running it unless you are fully aware of its operation. If this was a mistake, please disregard this message."
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoRespond(bot))
