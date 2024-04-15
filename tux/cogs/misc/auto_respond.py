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
]


class AutoRespond(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.content in harmful_commands:
            await message.reply(
                "Warning: This command is potentially harmful. Avoid running it unless you know what you are doing. If this was a mistake, please ignore this message."
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AutoRespond(bot))
