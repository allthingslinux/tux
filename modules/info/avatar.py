import mimetypes
from io import BytesIO

import discord
import httpx
from bot import Tux
from discord import app_commands
from discord.ext import commands
from utils.functions import generate_usage

client = httpx.AsyncClient()


class Avatar(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.prefix_avatar.usage = generate_usage(self.prefix_avatar)

    @app_commands.command(name="avatar")
    @app_commands.guild_only()
    async def slash_avatar(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ) -> None:
        """
        Get the global/server avatar for a member.

        Parameters
        ----------
        interaction : discord.Interaction
            The discord interaction object.
        member : discord.Member
            The member to get the avatar of.
        """

        await self.send_avatar(interaction, member)

    @commands.command(
        name="avatar",
        aliases=["av"],
    )
    @commands.guild_only()
    async def prefix_avatar(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member | None = None,
    ) -> None:
        """
        Get the global/server avatar for a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to get the avatar of.
        """

        await self.send_avatar(ctx, member)

    async def send_avatar(
        self,
        source: commands.Context[Tux] | discord.Interaction,
        member: discord.Member | None = None,
    ) -> None:
        """
        Send the global/server avatar for a member.

        Parameters
        ----------
        source : commands.Context[Tux] | discord.Interaction
            The source object for sending the message.
        member : discord.Member
            The member to get the avatar of.
        """
        if member is not None:
            guild_avatar = member.guild_avatar.url if member.guild_avatar else None
            global_avatar = member.avatar.url if member.avatar else None
            files = [await self.create_avatar_file(avatar) for avatar in [guild_avatar, global_avatar] if avatar]

            if files:
                if isinstance(source, discord.Interaction):
                    await source.response.send_message(files=files)
                else:
                    await source.reply(files=files)
            else:
                message = "Member has no avatar."
                if isinstance(source, discord.Interaction):
                    await source.response.send_message(content=message, ephemeral=True, delete_after=30)
                else:
                    await source.reply(content=message, ephemeral=True, delete_after=30)

        elif isinstance(source, commands.Context):
            member = await commands.MemberConverter().convert(source, str(source.author.id))

            guild_avatar = member.guild_avatar.url if member.guild_avatar else None
            global_avatar = member.avatar.url if member.avatar else None
            files = [await self.create_avatar_file(avatar) for avatar in [guild_avatar, global_avatar] if avatar]

            if files:
                await source.reply(files=files)
            else:
                await source.reply("You have no avatar.", ephemeral=True, delete_after=30)

    @staticmethod
    async def create_avatar_file(url: str) -> discord.File:
        """
        Create a discord file from an avatar url.

        Parameters
        ----------
        url : str
            The url of the avatar.

        Returns
        -------
        discord.File
            The discord file.
        """

        response = await client.get(url, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type")
        extension = mimetypes.guess_extension(content_type) or ".png"

        image_data = response.content
        image_file = BytesIO(image_data)
        image_file.seek(0)

        return discord.File(image_file, filename=f"avatar{extension}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Avatar(bot))
