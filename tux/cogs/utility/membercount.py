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
        """
        Show the member count for the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        if interaction.guild:
            # Get the member count for the server (total members)
            members = interaction.guild.member_count
            # Get the number of humans in the server (subtract bots from total members)
            humans = sum(not member.bot for member in interaction.guild.members)
            # Get the number of bots in the server (subtract humans from total members)
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

            logger.info(f"{interaction.user} used the membercount command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MemberCount(bot))
