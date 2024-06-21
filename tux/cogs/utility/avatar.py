from io import BytesIO

import discord
import httpx
from discord import app_commands
from discord.ext import commands
from loguru import logger

client = httpx.AsyncClient()


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
        guild_avatar = member.guild_avatar.url if member.guild_avatar else None
        profile_avatar = member.avatar.url if member.avatar else None

        files = [
            await self.create_avatar_file(avatar)
            for avatar in [guild_avatar, profile_avatar]
            if avatar
        ]

        if files:
            await interaction.response.send_message(files=files)
        else:
            await interaction.response.send_message(content="Member has no avatar.")

        logger.info(f"{interaction.user} used the avatar command in {interaction.channel}.")

    @staticmethod
    async def create_avatar_file(url: str) -> discord.File:
        """
        Create a discord file from an avatar url.

        Parameters:
        -----------
        url : str
            The url of the avatar.

        Returns:
        --------
        discord.File
            The discord file.
        """
        response = await client.get(url)
        response.raise_for_status()
        image_data = response.content
        image_file = BytesIO(image_data)
        image_file.seek(0)
        return discord.File(image_file, filename="avatar.png")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
