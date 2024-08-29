import discord
import httpx
from discord.ext import commands

client = httpx.AsyncClient()


class ExplainShell(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.API_URL = "https://www.mankier.com/api/v2/explain/?cols=500&q="

    @commands.command(name="explainshell", description="Get help for a shell command from explainshell.com")
    async def explain_shell(self, ctx: commands.Context, *, command: str) -> None:
        """
        Get help for a shell command from explainshell.com

        Parameters
        ----------
        ctx : commands.Context
            The context object of the command invocation.
        command : str
            The shell command to get help for.
        """

        async with ctx.typing():
            response = await client.get(f"{self.API_URL}{command}")

            if response.status_code != 200:
                return await ctx.send(f"An error occurred while fetching the data. Status code: {response.status_code}")

            content = response.text

            if not content:
                return await ctx.send("No results found for the given command.")

            lines = content.split("\n")
            if len(lines) < 2:
                return await ctx.send("Invalid response format from the API.")

            # Typically, the first line contains the title and the rest description
            title = lines[0]
            description = "\n".join(lines[1:])

            embed = discord.Embed(
                title=title,
                description=f"```{description}```",
                color=discord.Color.blue(),
            )

            await ctx.send(embed=embed)

            return None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ExplainShell(bot))
