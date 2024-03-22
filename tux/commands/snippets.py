import json

from discord.ext import commands

from tux.command_cog import CommandCog
from tux.main import TuxBot
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Snippet(CommandCog):
    @commands.hybrid_command(
        name="s",
        description="Get a snippet.",
        usage="s <name>",
    )
    async def snippet(self, ctx: commands.Context) -> None:
        """
        All Things Snippets, except it's actually only one thing snippets.
        """

        try:
            # open the snippets file
            with open("config/snippets.json") as file:
                snippets = json.load(file)
                # get the snippet name, if error, return
                try:
                    snippet_name = ctx.message.content.split(" ")[1]
                except IndexError:
                    await self.bot.embed.send_embed(
                        ctx.channel.id,
                        title="Error",
                        description="Please provide a snippet name.",
                    )
                    return

                # check if the snippet exists
                for snippet in snippets:
                    if snippet["name"] == snippet_name:
                        await self.bot.embed.send_embed(
                            ctx.channel.id,
                            title=snippet_name,
                            description=snippet["content"],
                        )
                        return

                await self.bot.embed.send_embed(
                    ctx.channel.id,
                    title="Error",
                    description=f"The snippet `{snippet_name}` does not exist.",
                )
                return
        except FileNotFoundError:
            await self.bot.embed.send_embed(
                ctx.channel.id,
                title="Error",
                description="The snippets file does not exist. Please copy the `config/snippets.json.example` file to `config/snippets.json` and add your snippets.",
            )
            return

    @commands.hybrid_command(
        name="ls",
        description="List all snippets.",
        usage="ls",
    )
    async def list_snippets(self, ctx: commands.Context) -> None:
        """
        Lists all snippets.
        """
        try:
            with open("config/snippets.json") as file:
                snippets = json.load(file)
                snippet_names = [snippet["name"] for snippet in snippets]
                await self.bot.embed.send_embed(
                    ctx.channel.id,
                    title="Snippets",
                    description="\n".join(snippet_names),
                )
        except FileNotFoundError:
            await self.bot.embed.send_embed(
                ctx.channel.id,
                title="Error",
                description="The snippets file does not exist. Please copy the `config/snippets.json.example` file to `config/snippets.json` and add your snippets.",
            )
            return

    @commands.hybrid_command(
        name="add-snippet",
        description="Add a snippet.",
        usage="add_snippet <name> <content>",
    )
    async def add_snippet(self, ctx: commands.Context) -> None:
        """
        Adds a snippet.
        """
        try:
            with open("config/snippets.json") as file:
                snippets = json.load(file)
                # get the snippet name, if error, return
                try:
                    snippet_name = ctx.message.content.split(" ")[1]
                    snippet_content = " ".join(ctx.message.content.split(" ")[2:])
                except IndexError:
                    await self.bot.embed.send_embed(
                        ctx.channel.id,
                        title="Error",
                        description="Please provide a snippet name and content.\nUsage: `add_snippet <name> <content>`",
                    )
                    return

                # check if the snippet exists
                for snippet in snippets:
                    if snippet["name"] == snippet_name:
                        await self.bot.embed.send_embed(
                            ctx.channel.id,
                            title="Error",
                            description=f"The snippet `{snippet_name}` already exists.",
                        )
                        return

                snippets.append({"name": snippet_name, "content": snippet_content})
                with open("config/snippets.json", "w") as file:
                    json.dump(snippets, file, indent=4)
                await self.bot.embed.send_embed(
                    ctx.channel.id,
                    title="Success",
                    description=f"The snippet `{snippet_name}` has been added.",
                )
        except FileNotFoundError:
            await self.bot.embed.send_embed(
                ctx.channel.id,
                title="Error",
                description="The snippets file does not exist. Please copy the `config/snippets.json.example` file to `config/snippets.json` and add your snippets.",
            )
            return


async def setup(bot: TuxBot) -> None:
    await bot.add_cog(Snippet(bot))
