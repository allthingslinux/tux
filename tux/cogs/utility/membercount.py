import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class MemberCount(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="membercount", description="Shows server member count")
    async def kick(
        self,
        interaction: discord.Interaction,
    ) -> None:
        logger.info(f"{interaction.user} showed the member count")

        if interaction.guild:
            members = interaction.guild.member_count
            embed = discord.Embed(
                title=f"Member count for {interaction.guild.name}",
                description=f"{members} members",
                color=discord.Color.green(),
            )
            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberCount(bot))
