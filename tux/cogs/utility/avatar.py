from io import BytesIO

import discord
import httpx
from discord import app_commands
from discord.ext import commands

client = httpx.AsyncClient()


class Avatar(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="avatar", description="Get the avatar of a member.")
    async def prefix_avatar(
        self,
        ctx: commands.Context[commands.Bot],
        member: discord.Member,
    ) -> None:
        """
        Get the avatar of a member.

        Parameters:
        -----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        member : discord.Member
            The member to get the avatar of.
        """
        await self.send_avatar(ctx, member)

    @app_commands.command(name="avatar", description="Get the avatar of a member.")
    @app_commands.describe(member="The member to get the avatar of.")
    async def slash_avatar(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """
        Get the avatar of a member.

        Parameters:
        -----------
        interaction : discord.Interaction
            The discord interaction object.
        member : discord.Member
            The member to get the avatar of.
        """
        await self.send_avatar(interaction, member)

    async def send_avatar(
        self,
        source: commands.Context[commands.Bot] | discord.Interaction,
        member: discord.Member,
    ) -> None:
        """
        Send the avatar of a member.

        Parameters
        ----------
        source : commands.Context[commands.Bot] | discord.Interaction
            The source object for sending the message.
        member : discord.Member
            The member to get the avatar of.
        """

        guild_avatar = member.guild_avatar.url if member.guild_avatar else None
        profile_avatar = member.avatar.url if member.avatar else None

        files = [await self.create_avatar_file(avatar) for avatar in [guild_avatar, profile_avatar] if avatar]

        if files:
            if isinstance(source, discord.Interaction):
                await source.response.send_message(files=files)
            else:
                await source.reply(files=files)
        else:
            message = "Member has no avatar."
            if isinstance(source, discord.Interaction):
                await source.response.send_message(content=message)
            else:
                await source.reply(content=message)

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
        response = await client.get(url, timeout=10)
        response.raise_for_status()

        image_data = response.content
        image_file = BytesIO(image_data)
        image_file.seek(0)

        return discord.File(image_file, filename="avatar.png")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Avatar(bot))
