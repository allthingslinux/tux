from datetime import UTC, datetime

import discord
from bot import Tux
from discord.ext import commands
from ui.embeds import EmbedCreator
from utils.functions import generate_usage, truncate

from . import SnippetsBaseCog


class SnippetInfo(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.snippet_info.usage = generate_usage(self.snippet_info)

    @commands.command(
        name="snippetinfo",
        aliases=["si"],
    )
    @commands.guild_only()
    async def snippet_info(self, ctx: commands.Context[Tux], name: str) -> None:
        """Display detailed information about a snippet.

        Shows the author, creation date, content/alias target, uses, and lock status.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to get information about.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)
        if not snippet:
            return

        # Attempt to resolve author, default to showing ID if not found
        author = self.bot.get_user(snippet.snippet_user_id)
        author_display = author.mention if author else f"<@!{snippet.snippet_user_id}> (Not found)"

        # Attempt to get aliases if any
        aliases = [alias.snippet_name for alias in (await self.db.snippet.get_all_aliases(name, ctx.guild.id))]

        # Determine content field details
        content_field_name = "Alias Target" if snippet.alias else "Content Preview"
        content_field_value = f"{snippet.alias or snippet.snippet_content}"

        # Create and populate the info embed
        embed: discord.Embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.DEFAULT,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Snippet Information",
            message_timestamp=snippet.snippet_created_at or datetime.fromtimestamp(0, UTC),
        )

        embed.add_field(name="Name", value=snippet.snippet_name, inline=True)
        embed.add_field(name="Aliases", value=", ".join(f"`{alias}`" for alias in aliases), inline=True)
        embed.add_field(name="Author", value=author_display, inline=True)
        embed.add_field(name="Uses", value=str(snippet.uses), inline=True)  # Ensure string
        embed.add_field(name="Locked", value="Yes" if snippet.locked else "No", inline=True)

        embed.add_field(
            name=content_field_name,
            value=f"> -# {truncate(text=content_field_value, length=256)}",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Load the SnippetInfo cog."""
    await bot.add_cog(SnippetInfo(bot))
