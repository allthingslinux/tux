import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from tux.utils.embeds import EmbedCreator


class MemberCount(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="membercount", description="Shows server member count")
    async def membercount(
        self,
        interaction: discord.Interaction,
    ) -> None:
        logger.info(f"{interaction.user} showed the member count")

        if interaction.guild:
            members = interaction.guild.member_count
            humans = sum(member.bot for member in interaction.guild.members if not member.bot)
            bots = sum(member.bot for member in interaction.guild.members if member.bot)

            embed = EmbedCreator.create_info_embed(
                title="Member Count",
                description="Here is the member count for the server.",
                interaction=interaction,
            )

            embed.add_field(name="Members", value=str(members))
            embed.add_field(name="Humans", value=str(humans))
            embed.add_field(name="Bots", value=str(bots))

            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberCount(bot))
