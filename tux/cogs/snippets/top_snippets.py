from discord.ext import commands

from prisma.models import Snippet
from tux.bot import Tux
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils.constants import CONST
from tux.utils.flags import generate_usage

from . import SnippetsBaseCog


class TopSnippets(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.top_snippets.usage = generate_usage(self.top_snippets)

    @commands.command(
        name="topsnippets",
        aliases=["ts"],
    )
    @commands.guild_only()
    async def top_snippets(self, ctx: commands.Context[Tux]) -> None:
        """Display the most used snippets in the server.

        Shows the top snippets based on usage count in descending order.
        Currently limited to the top N snippets defined by SNIPPET_PAGINATION_LIMIT.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        """
        assert ctx.guild

        # Fetch all snippets for the guild
        snippets: list[Snippet] = await self.db.snippet.get_all_snippets_by_guild_id(ctx.guild.id)

        if not snippets:
            await self.send_snippet_error(ctx, description="No snippets found in this server.")
            return

        # Sort by usage count (most used first)
        snippets.sort(key=lambda s: s.uses, reverse=True)

        # Format the top snippets into a code block description
        top_snippet_lines = (
            f"{i + 1}. {s.snippet_name:<20} | uses: {s.uses}"
            for i, s in enumerate(snippets[: CONST.SNIPPET_PAGINATION_LIMIT])
        )

        description_text = f"```\n{'\n'.join(top_snippet_lines)}\n```"

        # Create the embed
        # TODO: Consider adding pagination if the list becomes very long

        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.DEFAULT,
            title="Top Snippets",
            description=description_text,
            hide_author=True,
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    """Load the TopSnippets cog."""
    await bot.add_cog(TopSnippets(bot))
