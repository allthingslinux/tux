import random

from discord.ext import commands

from tux.bot import Tux
from tux.ui.embeds import EmbedCreator
from tux.utils.functions import generate_usage


class Random(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.random.usage = generate_usage(self.random)
        self.coinflip.usage = generate_usage(self.coinflip)
        self.eight_ball.usage = generate_usage(self.eight_ball)
        self.dice.usage = generate_usage(self.dice)
        self.random_number.usage = generate_usage(self.random_number)

    @commands.hybrid_group(
        name="random",
        aliases=["rand"],
    )
    @commands.guild_only()
    async def random(self, ctx: commands.Context[Tux]) -> None:
        """
        Random generation commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("random")

    @random.command(
        name="coinflip",
        aliases=["cf"],
    )
    @commands.guild_only()
    async def coinflip(self, ctx: commands.Context[Tux]) -> None:
        """
        Flip a coin.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        """

        await ctx.send(
            content="You got heads!" if random.choice([True, False]) else "You got tails!",
        )

    @random.command(
        name="8ball",
        aliases=["eightball", "8b"],
    )
    @commands.guild_only()
    async def eight_ball(
        self,
        ctx: commands.Context[Tux],
        *,
        question: str,
        cow: bool = False,
    ) -> None:
        """
        Ask the magic 8ball a question.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        question : str
            The question to ask the 8ball.
        cow : bool, optional
            Whether to use the cow ASCII art, by default False.
        """

        responses = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes definitely",
            "You may rely on it",
            "As I see it yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Probably",
            "Outlook not so good",
            "Very doubtful",
            "Why the hell are you asking me lmao",
            "What???",
            "Hell yeah",
            "Hell no",
            "When pigs fly",
            "Ask someone else for once, I'm sick and tired of answering your questions you absolute buffoon.",
            "I dont know, ask me later",
            "I'm not sure",
            "Ask your mom",
            "Ask Puffy or Beastie",
            "Absolutely",
            "Absolutely not",
            "You're joking right?",
            "Ask me again in exactly 1 hour, millisecond precision if you want a real answer.",
            "Ask a real person.",
            "I may be a robot but some questions are just too stupid to answer.",
        ]

        choice = random.choice(responses)

        if len(question) > 120:
            response = """  _________________________________________
< That question is too long! Try a new one. >
  -----------------------------------------
   \\
    \\
        .--.
       |o_o |
       |:_/ |
      //   \\ \\
     (|     | )
    /'\\_   _/`\\
    \\___)=(___/
"""
        elif cow:
            response = f"""Response to "{question}":
  {"_" * len(choice)}
< {choice} >
  {"-" * len(choice)}
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""
        else:
            response = f"""Response to "{question}":
  {"_" * len(choice)}
< {choice} >
  {"-" * len(choice)}
   \\
    \\
        .--.
       |o_o |
       |:_/ |
      //   \\ \\
     (|     | )
    /'\\_   _/`\\
    \\___)=(___/
"""
        await ctx.send(content=f"```{response}```")

    @random.command(
        name="dice",
        aliases=["d"],
    )
    @commands.guild_only()
    async def dice(self, ctx: commands.Context[Tux], sides: int = 6) -> None:
        """
        Roll a dice.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        sides : int, optional
            The number of sides on the dice, by default 6.
        """

        if sides < 2:
            await ctx.send(content="The dice must have at least 2 sides.", ephemeral=True, delete_after=30)
            return

        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.INFO,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title=f"Dice Roll (D{sides})",
            description=f"You rolled a {random.randint(1, sides)}!",
        )

        await ctx.send(embed=embed)

    @random.command(
        name="number",
        aliases=["n"],
    )
    @commands.guild_only()
    async def random_number(
        self,
        ctx: commands.Context[Tux],
        minimum_str: str = "0",
        maximum_str: str = "100",
    ) -> None:
        """
        Generate a random number between two values.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        minimum_str : str, optional
            The minimum value of the random number, by default 0. Converted to int after removing certain characters.
        maximum_str : str, optional
            The maximum value of the random number, by default 100. Converted to int after removing certain characters.

        """
        try:
            minimum_int = int(minimum_str.replace(",", "").replace(".", ""))
            maximum_int = int(maximum_str.replace(",", "").replace(".", ""))
        except ValueError:
            await ctx.send(
                content="Invalid input for minimum or maximum value. Please provide valid numbers.",
                ephemeral=True,
                delete_after=30,
            )
            return

        if minimum_int > maximum_int:
            await ctx.send(
                content="The minimum value must be less than the maximum value.",
                ephemeral=True,
                delete_after=30,
            )
            return

        await ctx.send(content=f"Your random number is: {random.randint(minimum_int, maximum_int)}")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Random(bot))
