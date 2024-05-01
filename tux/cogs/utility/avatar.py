import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="avatar", description="Get the avatar of a member.")
    @app_commands.describe(member="The member to get the avatar of.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """
        Get the avatar of a member.

        Parameters:
        -----------
        interaction : discord.Interaction
            The discord interaction object.
        member : discord.Member
            The member to get the avatar of.
        """

        avatar = member.avatar.url if member.avatar else "Member has no avatar."

        await interaction.response.send_message(content=avatar)

        logger.info(f"{interaction.user} used the avatar command in {interaction.channel}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
