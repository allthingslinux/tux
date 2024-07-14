import discord
from discord.ext import commands
from loguru import logger

from tux.services import xkcd
from tux.utils.embeds import EmbedCreator


class XkcdLinkButtons(discord.ui.View):
    def __init__(self, explain_url: str, webpage_url: str) -> None:
        super().__init__()
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Explainxkcd", url=explain_url),
        )
        self.add_item(
            discord.ui.Button(style=discord.ButtonStyle.link, label="Webpage", url=webpage_url),
        )


class Xkcd(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.client = xkcd.Client()

    @commands.hybrid_group(name="xkcd", aliases=["xk"])
    @commands.guild_only()
    async def xkcd(self, ctx: commands.Context[commands.Bot], comic_id: int | None = None) -> None:
        """
        xkcd related commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        comic_id : int | None
            The ID of the xkcd comic to search for.
        """

        if comic_id:
            await self.specific(ctx, comic_id)
        else:
            await ctx.send_help("xkcd")

    @xkcd.command(name="latest", aliases=["l", "new", "n"])
    @commands.guild_only()
    async def latest(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Get the latest xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        """

        embed, view, ephemeral = await self.get_comic_and_embed(latest=True)

        if view:
            await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.reply(embed=embed, ephemeral=ephemeral)

    @xkcd.command(name="random", aliases=["rand", "r"])
    @commands.guild_only()
    async def random(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Get a random xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the
        """

        embed, view, ephemeral = await self.get_comic_and_embed()

        if view:
            await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.reply(embed=embed, ephemeral=ephemeral)

    @xkcd.command(name="specific", aliases=["s", "id", "i", "#", "num"])
    @commands.guild_only()
    async def specific(self, ctx: commands.Context[commands.Bot], comic_id: int) -> None:
        """
        Get a specific xkcd comic.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        comic_id : int
            The ID of the comic to search for.
        """

        embed, view, ephemeral = await self.get_comic_and_embed(number=comic_id)

        if view:
            await ctx.reply(embed=embed, view=view, ephemeral=ephemeral)
        else:
            await ctx.reply(embed=embed, ephemeral=ephemeral)

    async def get_comic_and_embed(
        self,
        latest: bool = False,
        number: int | None = None,
    ) -> tuple[discord.Embed, discord.ui.View | None, bool]:
        """
        Get the xkcd comic and create an embed.
        """
        try:
            if latest:
                comic = self.client.get_latest_comic(raw_comic_image=True)
            elif number:
                comic = self.client.get_comic(number, raw_comic_image=True)
            else:
                comic = self.client.get_random_comic(raw_comic_image=True)

            embed = EmbedCreator.create_success_embed(
                title="",
                description=f"\n\n> {comic.description.strip()}" if comic.description else "",
            )

            embed.set_author(name=f"xkcd {comic.id} - {comic.title}")
            embed.set_image(url=comic.image_url)
            ephemeral = False

        except xkcd.HttpError:
            logger.error("HTTP error occurred while fetching xkcd comic")
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="I couldn't find the xkcd comic. Please try again later.",
            )
            ephemeral = True
            return embed, None, ephemeral

        except Exception as e:
            logger.error(f"Error getting xkcd comic: {e}")
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="An error occurred while fetching the xkcd comic",
            )
            ephemeral = True
            return embed, None, ephemeral

        else:
            return (
                embed,
                XkcdLinkButtons(str(comic.explanation_url), str(comic.comic_url)),
                ephemeral,
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Xkcd(bot))
