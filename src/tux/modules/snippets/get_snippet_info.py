"""
Get snippet information commands.

This module provides functionality for displaying detailed information
about existing code snippets in Discord guilds.
"""

from datetime import UTC, datetime

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.shared.functions import truncate
from tux.ui.embeds import EmbedCreator

from . import SnippetsBaseCog


class SnippetInfo(SnippetsBaseCog):
    """Discord cog for displaying snippet information."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the snippet info cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

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
        author_display = (
            author.mention if author else f"<@!{snippet.snippet_user_id}> (Not found)"
        )

        # Get aliases that point to this snippet (if any)
        aliases = [
            alias.snippet_name
            for alias in await self.db.snippet.get_snippets_by_alias(
                snippet.snippet_name,
                ctx.guild.id,
            )
        ]

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
            message_timestamp=datetime.fromtimestamp(
                0,
                UTC,
            ),  # Snippet model doesn't have created_at
        )

        embed.add_field(name="Name", value=snippet.snippet_name, inline=True)
        embed.add_field(
            name="Aliases",
            value=", ".join(f"`{alias}`" for alias in aliases) if aliases else "None",
            inline=True,
        )
        embed.add_field(name="Author", value=author_display, inline=True)
        embed.add_field(
            name="Uses",
            value=str(snippet.uses),
            inline=True,
        )
        embed.add_field(
            name="Locked",
            value="Yes" if snippet.locked else "No",
            inline=True,
        )
        embed.add_field(
            name=content_field_name,
            value=f"> -# {truncate(text=content_field_value, length=256)}",
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Load the SnippetInfo cog."""
    await bot.add_cog(SnippetInfo(bot))
