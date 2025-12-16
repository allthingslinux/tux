"""
Get snippet commands.

This module provides functionality for retrieving and displaying
existing code snippets from Discord guilds.
"""

from typing import Final

from discord import AllowedMentions, Message
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from tux.core.bot import Tux

from . import SnippetsBaseCog

# Snippet pagination limit (Discord's actual max is 4096, but we paginate at 2000 for better UX)
SNIPPET_MESSAGE_PAGINATION_LIMIT: Final[int] = 2000


class Snippet(SnippetsBaseCog):
    """Discord cog for retrieving snippets."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the get snippet cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.command(
        name="snippet",
        aliases=["s"],
    )
    @commands.guild_only()
    async def snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """Retrieve and display a snippet's content.

        If the snippet is an alias, it resolves the alias and displays the
        target snippet's content, indicating the alias relationship.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to retrieve.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)
        if not snippet:
            return

        # Increment uses before potentially resolving alias
        try:
            snippet_id = self._require_snippet_id(snippet)
            await self.db.snippet.increment_snippet_uses(snippet_id)
        except ValueError:
            await self.send_snippet_error(ctx, description="Snippet ID is invalid.")
            return

        # Resolve alias if needed
        target_snippet, is_alias = await self._resolve_alias(snippet, ctx.guild.id)

        # Handle broken alias
        if is_alias and target_snippet is None:
            try:
                await self.db.snippet.delete_snippet_by_id(snippet_id)
                await self.send_snippet_error(
                    ctx,
                    description=f"Alias `{snippet.snippet_name}` points to a non-existent snippet (`{snippet.alias}`). Deleting alias.",
                )
                logger.info(
                    f"Deleted broken alias '{snippet.snippet_name}' pointing to '{snippet.alias}'",
                )
            except Exception as e:
                logger.error(f"Failed to delete broken alias: {e}")
                await self.send_snippet_error(
                    ctx,
                    description="Failed to clean up broken alias.",
                )
            return

        # At this point, target_snippet is guaranteed to be SnippetModel (not None)
        # because we handle the None case above and return early
        if is_alias:
            assert (
                target_snippet is not None
            )  # Type guard: we already checked for None above
            display_snippet = target_snippet
        else:
            display_snippet = snippet

        # Format message using helper method
        text = self._format_snippet_message(
            display_snippet,
            is_alias=is_alias,
            alias_name=snippet.snippet_name if is_alias else None,
        )

        # Send message or paginate if text exceeds pagination limit
        if len(text) <= SNIPPET_MESSAGE_PAGINATION_LIMIT:
            # Check if there is a message being replied to
            reference = getattr(ctx.message.reference, "resolved", None)
            # Set reply target if it exists, otherwise use the context message
            reply_target = reference if isinstance(reference, Message) else ctx

            await reply_target.reply(
                text,
                allowed_mentions=AllowedMentions(
                    users=False,
                    roles=False,
                    everyone=False,
                    replied_user=True,
                ),
            )
            return

        menu = ViewMenu(
            ctx,
            menu_type=ViewMenu.TypeText,
            all_can_click=True,
            show_page_director=False,
            timeout=180,
            delete_on_timeout=True,
        )

        for i in range(0, len(text), SNIPPET_MESSAGE_PAGINATION_LIMIT):
            page: str = text[i : i + SNIPPET_MESSAGE_PAGINATION_LIMIT]
            menu.add_page(content=page)

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()


async def setup(bot: Tux) -> None:
    """Load the Snippet cog."""
    await bot.add_cog(Snippet(bot))
