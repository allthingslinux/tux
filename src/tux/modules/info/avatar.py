import mimetypes
from io import BytesIO

import discord
from discord.ext import commands

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.http_client import http_client
from tux.shared.constants import CONST


class Avatar(BaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)

    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "pfp"],
        description="Get the global/server avatar for a member.",
    )
    @commands.guild_only()
    async def avatar(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member | None = None,
    ) -> None:
        """
        Get the global/server avatar for a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        member : discord.Member | None
            The member to get the avatar of. If None, uses the command author.
        """

        await self.send_avatar(ctx, member)

    async def send_avatar(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member | None = None,
    ) -> None:
        """
        Send the global/server avatar for a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The discord context object.
        member : discord.Member | None
            The member to get the avatar of. If None, uses the context author.
        """

        # If no member specified, use the command author
        if member is None:
            # Convert author to Member if possible, otherwise handle as User
            if isinstance(ctx.author, discord.Member):
                member = ctx.author
            else:
                # For DMs or other contexts where author is not a Member
                await ctx.send("This command can only be used in servers.", ephemeral=True)
                return

        guild_avatar = member.guild_avatar.url if member.guild_avatar else None
        global_avatar = member.avatar.url if member.avatar else None

        files = [await self.create_avatar_file(avatar) for avatar in [guild_avatar, global_avatar] if avatar]

        if files:
            await ctx.send(files=files)
        else:
            message = f"{member.display_name} has no avatar." if member != ctx.author else "You have no avatar."

            await ctx.send(content=message, ephemeral=True, delete_after=CONST.DEFAULT_DELETE_AFTER)

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

        Raises
        ------
        RuntimeError
            If the avatar cannot be fetched or processed.
        """
        try:
            response = await http_client.get(url, timeout=CONST.HTTP_TIMEOUT)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type")
            extension = mimetypes.guess_extension(content_type) or CONST.FILE_EXT_PNG

            image_data = response.content
            image_file = BytesIO(image_data)
            image_file.seek(0)

            return discord.File(image_file, filename=f"avatar{extension}")

        except Exception as e:
            msg = f"Failed to fetch avatar from {url}"
            raise RuntimeError(msg) from e


async def setup(bot: Tux) -> None:
    await bot.add_cog(Avatar(bot))
