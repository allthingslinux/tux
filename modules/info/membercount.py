import discord
from bot import Tux
from discord import app_commands
from discord.ext import commands
from ui.embeds import EmbedCreator


class MemberCount(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @app_commands.command(name="membercount", description="Shows server member count")
    async def membercount(self, interaction: discord.Interaction) -> None:
        """
        Show the member count for the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        """

        assert interaction.guild

        # Get the member count for the server (total members)
        members = interaction.guild.member_count
        # Get the number of humans in the server (subtract bots from total members)
        humans = sum(not member.bot for member in interaction.guild.members)
        # Get the number of bots in the server (subtract humans from total members)
        bots = sum(member.bot for member in interaction.guild.members if member.bot)
        # Get the number of staff members in the server
        staff_role = discord.utils.get(interaction.guild.roles, name="%wheel")
        staff = len(staff_role.members) if staff_role else 0

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=interaction.user.name,
            user_display_avatar=interaction.user.display_avatar.url,
            title="Member Count",
            description="Here is the member count for the server.",
        )

        embed.add_field(name="Members", value=str(members), inline=False)
        embed.add_field(name="Humans", value=str(humans), inline=True)
        embed.add_field(name="Bots", value=str(bots), inline=True)
        if staff > 0:
            embed.add_field(name="Staff", value=str(staff), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(MemberCount(bot))
