"""
Xkcd comic viewing commands.

This module provides commands to fetch and display xkcd comics, including the
latest comic, random comics, and specific comics by ID. Comics are displayed
with interactive buttons for navigation to the comic's explanation and original page.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.wrappers import xkcd
from tux.ui.buttons import XkcdButtons
from tux.ui.embeds import EmbedCreator


class Xkcd(BaseCog):
    """Discord cog for xkcd comic viewing commands.

    Provides commands to fetch and display xkcd comics from the xkcd webcomic.
    Supports viewing the latest comic, random comics, and specific comics by ID.
    Comics are displayed with navigation buttons to the explanation and original pages.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Xkcd cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        self.client = xkcd.Client()

    @commands.hybrid_group(
        name="xkcd",
        aliases=["xk"],
    )
    @commands.guild_only()
    async def xkcd(
        self,
        ctx: commands.Context[Tux],
        comic_id: int | None = None,
    ) -> None:
        """
        Xkcd related commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        comic_id : int | None
            The ID of the xkcd comic to search for.
        """
        if comic_id:
            await self.specific(ctx, comic_id)
        else:
            await ctx.send_help("xkcd")

    @xkcd.command(
        name="latest",
        aliases=["l", "new", "n"],
    )
    @commands.guild_only()
    async def latest(self, ctx: commands.Context[Tux]) -> None:
        """
        Get the latest xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """
        embed, view, ephemeral = await self.get_comic_and_embed(latest=True)

        if view:
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @xkcd.command(
        name="random",
        aliases=["rand", "r"],
    )
    @commands.guild_only()
    async def random(self, ctx: commands.Context[Tux]) -> None:
        """
        Get a random xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the
        """
        embed, view, ephemeral = await self.get_comic_and_embed()

        if view:
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.send(embed=embed, ephemeral=ephemeral)

    @xkcd.command(
        name="specific",
        aliases=["s", "id", "num"],
    )
    @commands.guild_only()
    async def specific(self, ctx: commands.Context[Tux], comic_id: int) -> None:
        """
        Get a specific xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        comic_id : int
            The ID of the comic to search for.
        """
        embed, view, ephemeral = await self.get_comic_and_embed(number=comic_id)

        if view:
            await ctx.send(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.send(embed=embed, ephemeral=ephemeral)

    async def get_comic_and_embed(
        self,
        latest: bool = False,
        number: int | None = None,
    ) -> tuple[discord.Embed, discord.ui.View | None, bool]:
        """
        Get the xkcd comic and create an embed.

        Returns
        -------
        tuple[discord.Embed, discord.ui.View | None, bool]
            Tuple of (embed, view, success_flag).
        """
        try:
            if latest:
                comic = self.client.get_latest_comic(raw_comic_image=True)
            elif number:
                comic = self.client.get_comic(number, raw_comic_image=True)
            else:
                comic = self.client.get_random_comic(raw_comic_image=True)

            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.INFO,
                title="",
                description=f"\n\n> {comic.description.strip()}"
                if comic.description
                else "",
                custom_author_text=f"xkcd {comic.id} - {comic.title}",
                image_url=comic.image_url,
            )

            ephemeral = False

        except xkcd.HttpError:
            logger.error("HTTP error occurred while fetching xkcd comic")
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                description="I couldn't find the xkcd comic. Please try again later.",
            )
            ephemeral = True
            return embed, None, ephemeral

        except Exception as e:
            logger.error(f"Error getting xkcd comic: {e}")
            embed = EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedCreator.ERROR,
                description="An error occurred while fetching the xkcd comic",
            )
            ephemeral = True
            return embed, None, ephemeral

        else:
            return (
                embed,
                XkcdButtons(str(comic.explanation_url), str(comic.comic_url)),
                ephemeral,
            )


async def setup(bot: Tux) -> None:
    """Set up the Xkcd cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Xkcd(bot))
