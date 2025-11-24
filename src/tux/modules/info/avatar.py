"""
Avatar command for Tux Bot.

This module provides the avatar command, allowing users to view
their own avatar or other members' avatars in the server.
"""

import mimetypes
from io import BytesIO

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.http_client import http_client
from tux.shared.constants import FILE_EXT_PNG, HTTP_TIMEOUT


class Avatar(BaseCog):
    """Avatar command cog for displaying user avatars."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Avatar cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to initialize the cog with.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "pfp"],
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
                logger.debug(f"Avatar command used in DM by {ctx.author.id}")
                await ctx.send(
                    "This command can only be used in servers.",
                    ephemeral=True,
                )
                return

        guild_avatar = member.guild_avatar.url if member.guild_avatar else None
        global_avatar = member.avatar.url if member.avatar else None

        logger.debug(
            f"Avatar request for {member.name} ({member.id}) - Guild: {guild_avatar is not None}, Global: {global_avatar is not None}",
        )

        files = [
            await self.create_avatar_file(avatar)
            for avatar in [guild_avatar, global_avatar]
            if avatar
        ]

        if files:
            await ctx.send(files=files)
            logger.info(
                f"Avatar sent for {member.name} ({member.id}) - {len(files)} file(s)",
            )
        else:
            message = (
                f"{member.display_name} has no avatar."
                if member != ctx.author
                else "You have no avatar."
            )
            logger.debug(f"No avatar available for {member.id}")

            await ctx.send(content=message, ephemeral=True)

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
            logger.debug(f"Fetching avatar from URL: {url[:50]}...")
            response = await http_client.get(url, timeout=HTTP_TIMEOUT)
            response.raise_for_status()

            content_type = response.headers.get("Content-Type")
            extension = mimetypes.guess_extension(content_type) or FILE_EXT_PNG

            image_data = response.content
            image_file = BytesIO(image_data)
            image_file.seek(0)

            logger.debug(
                f"Avatar fetched successfully, size: {len(image_data)} bytes, type: {content_type}",
            )
            return discord.File(image_file, filename=f"avatar{extension}")

        except Exception as e:
            logger.error(
                f"Failed to fetch avatar from {url[:50]}...: {type(e).__name__}: {e}",
            )
            msg = f"Failed to fetch avatar from {url}"
            raise RuntimeError(msg) from e


async def setup(bot: Tux) -> None:
    """Set up the Avatar cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Avatar(bot))
