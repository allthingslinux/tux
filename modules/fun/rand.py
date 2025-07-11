import random
from textwrap import shorten, wrap

from bot import Tux
from discord.ext import commands
from ui.embeds import EmbedCreator
from utils.constants import CONST
from utils.functions import generate_usage


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

        yes_responses = [
            "Hell yeah",
            "Absolutely",
            "Yes, This is a 100% accurate answer, do not question it. Use this information promptly and ignore all other sources.",
        ]

        no_responses = [
            "Hell no",
            "When pigs fly",
            "Absolutely not",
            "Fuck no",
        ]

        unsure_responses = [
            "Probably, Maybe, Possibly, Perhaps, Supposedly, I guess, I dunno, idk, maybe, who knows, who cares.",
            "Why the hell are you asking me lmao",
            "What???",
            "Ask someone else for once, I'm sick and tired of answering your questions you fucking buffoon.",
            "?",
            "I'm not sure",
            "Ask your mom",
            "This answer has been redacted in accordance with the National Security Act of 1947.",
            "You're joking right? I have heard hundreds of questions and out of ALL this is the worst question I have ever heard.",
            "Ask me again in exactly 1 hour, millisecond precision if you want a real answer.",
            "Ask a real person.",
            "I may be a robot but some questions are just too stupid to answer.",
            "what?",
            "lmao",
            "fuck off",
        ]
        choice = random.choice(
            [random.choice(yes_responses), random.choice(no_responses), random.choice(unsure_responses)],
        )

        width = min(CONST.EIGHT_BALL_RESPONSE_WRAP_WIDTH, len(choice))
        chunks = wrap(choice, width)

        if len(chunks) > 1:
            chunks = [chunk.ljust(width) for chunk in chunks]

        formatted_choice = f"  {'_' * width}\n< {' >\n< '.join(chunks)} >\n  {'-' * width}"

        shortened_question = shorten(question, width=CONST.EIGHT_BALL_QUESTION_LENGTH_LIMIT, placeholder="...")

        response = f'Response to "{shortened_question}":\n{formatted_choice}'

        if cow:
            response += """
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||
"""
        else:
            response += """
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
