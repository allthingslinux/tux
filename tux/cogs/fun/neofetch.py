import time

import discord
import psutil  # for uptime
from discord import app_commands
from discord.ext import commands

gray = "[1;30m"
red = "[1;31m"
green = "[1;32m"
yellow = "[1;33m"
blue = "[1;34m"
pink = "[1;35m"
cyan = "[1;36m"
white = "[1;37m"
reset = "[0;0m"


class Neofetch(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="neofetch", description="Make a neofetch.")
    async def neofetch(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                content="This command cannot be used in direct messages.", ephemeral=True
            )
            return

        # base ascii art
        base = """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣶⣾⣿⢿⣿⣶⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣟⣯⣷⢿⣻⣷⣻⡾⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡿⣽⣟⣾⢿⣻⡾⣯⡿⣯⡿⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠋⠙⢽⣟⡟⠁⠀⠙⣿⢯⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣇⢸⣧⡸⠿⣀⢼⣿⠀⢸⣿⢷⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠜⢍⢊⢂⠢⠩⡙⠤⣿⣟⡿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣧⡣⣂⢂⠢⢡⠱⡘⣑⢼⣯⡿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣼⣿⠈⠲⢌⣍⡢⠕⠈⠁⠈⣿⣽⡿⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⡍⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣷⢿⣻⣷⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣠⣿⣯⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣟⢯⣿⣽⣆⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣴⣿⣳⣯⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣷⡽⣾⣟⣧⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⣼⣿⢳⣯⠃⠀⠀⠀⢀⠠⠀⠂⠄⠠⠀⠀⠀⠀⠀⢿⣽⡼⣯⡿⣧⠀⠀⠀⠀
⠀⠀⠀⠀⠀⣸⡿⡇⣿⠇⠀⠀⠀⠂⠄⠂⡈⠄⠈⠄⡈⠄⠂⠀⠀⠈⣿⡇⣿⣻⣟⡇⠀⠀⠀
⠀⠀⠀⠀⠀⣿⣟⡇⣿⠀⠀⢀⠁⡈⠄⠁⠄⠂⡁⠄⠐⢀⠡⠐⠀⠀⠙⠃⢿⣯⢿⣻⠀⠀⠀
⠀⠀⠀⠀⢸⣿⣽⣧⡘⠀⠀⡂⠄⠐⡈⠐⡈⠠⠀⢂⠁⠄⠐⡈⢀⣼⣿⣿⣷⣮⢻⡿⠀⠀⠀
⠀⠀⠀⢀⠞⢅⠢⡙⢿⣦⣀⠂⠄⢁⠐⠠⠐⢀⠁⠄⠐⡀⢁⢰⢋⠺⣟⣾⢷⠻⡛⡣⡄⠀⠀
⢀⢔⠞⠍⢌⠢⡑⠄⠍⢿⣽⣷⣄⠂⠐⡀⠡⢀⠐⢈⠠⠀⠂⡼⡂⠕⠌⠍⢅⢑⢐⢐⢹⠀⠀
⢺⠠⠡⡑⢄⠑⠌⠌⠌⢌⢳⣿⣽⡆⠁⠄⢂⠠⠈⠠⠐⢈⠀⡗⡨⠨⠨⡈⡂⡂⡂⠢⠡⣣⡀
⢸⠡⡑⢌⠢⠡⠡⠡⡑⡐⡐⡹⣌⠠⠈⠄⠂⡀⠅⠂⡁⠄⣰⠣⠨⡈⡂⡂⡂⡂⠪⡈⡂⡂⣳
⡏⢌⢂⠢⠡⠡⠡⡑⡐⡐⡐⡐⠌⣷⣤⣌⣀⣐⣀⣥⣴⣾⡟⢌⢂⢂⠢⡂⠪⡈⣂⣢⠶⠚⠁
⠙⠲⠦⠥⢥⣅⡕⡐⡐⡐⡐⠌⢌⡾⠟⠟⠛⠛⠛⠛⠽⠾⣇⢂⢂⠢⡑⢌⢂⡶⠋⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠑⠒⠶⠬⠞⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠢⣆⣑⡬⠖⠋⠀⠀⠀⠀⠀⠀"""

        # get uptime in the format of days, hours, minutes
        uptime = time.strftime("%d days, %H hours, %M minutes", time.gmtime(time.time() - psutil.boot_time()))
        cpuusage = psutil.cpu_percent()
        memusage = psutil.virtual_memory().percent

        lines = f"""{yellow}tux{reset}@{yellow}{interaction.guild.name.lower().replace(" ", "")}{reset}
------------------ 
[1;4;36;40mTux Stats{reset}
{red}OS{reset}: Tux Alpha
{yellow}Kernel{reset}: 6.9
{green}Uptime{reset}: {uptime}
{cyan}CPU{reset}: {cpuusage}%
{blue}Memory{reset}: {memusage}%
{pink}Ping{reset}: {round(self.bot.latency * 1000)}ms
------------------ 
[1;4;36;40mServer Stats{reset}
{red}Name{reset}: {interaction.guild.name}
{yellow}Owner{reset}: {interaction.guild.owner}
{green}Members{reset}: {interaction.guild.member_count}
{cyan}Roles{reset}: {len(interaction.guild.roles)}
{blue}Channels{reset}: {len(interaction.guild.channels)}
{pink}Emojis + Stickers{reset}: {len(interaction.guild.emojis) + len(interaction.guild.stickers)}
------------------
"""

        fetch = (
            "\n".join([f"{base.splitlines()[i]}  {lines.splitlines()[i]}" for i in range(len(lines.splitlines()))])
            + "\n"
            + "\n".join(base.splitlines()[len(lines.splitlines()) :])
        )

        await interaction.response.send_message(content=f"```ansi\n{fetch}\n```")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Neofetch(bot))
